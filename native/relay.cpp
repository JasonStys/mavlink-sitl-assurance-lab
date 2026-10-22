// Jason Stys: Linux loopback-only fixed-port simulator fault relay. Functions/state: docs/SOURCE_MAP.md.
#include "fault.hpp"
#include <arpa/inet.h>
#include <array>
#include <chrono>
#include <iostream>
#include <poll.h>
#include <sstream>
#include <stdexcept>
#include <sys/socket.h>
#include <unistd.h>

namespace {
// This socket has no destination/IP CLI and cannot bind a public interface.
class LoopbackSocket {
  public:
    int fd = -1;
    LoopbackSocket() {
        fd = socket(AF_INET, SOCK_DGRAM, 0);
        if (fd < 0) throw std::runtime_error("Cannot create owned UDP socket");
        auto address = endpoint(14540);
        if (bind(fd, reinterpret_cast<sockaddr*>(&address), sizeof(address)) != 0) {
            close(fd); fd = -1;
            throw std::runtime_error("Fixed loopback port 14540 unavailable; refusing attachment");
        }
    }
    ~LoopbackSocket() { if (fd >= 0) close(fd); }
    LoopbackSocket(const LoopbackSocket&) = delete;
    LoopbackSocket& operator=(const LoopbackSocket&) = delete;
    // Only the two reviewed peer ports can be selected by the caller.
    static sockaddr_in endpoint(std::uint16_t port) {
        sockaddr_in address{};
        address.sin_family = AF_INET;
        address.sin_port = htons(port);
        address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
        return address;
    }
};

// Protocol metadata, never raw payload, credentials, endpoints or arbitrary control text.
void packet_event(const char* event, std::uint64_t now, bool downstream,
                  std::span<const std::uint8_t> packet, const std::string& reason,
                  std::uint64_t packet_id) {
    const auto framing = lab::inspect(packet);
    std::cout << "{\"event\":\"" << event << "\",\"at_ms\":" << now
              << ",\"packet_id\":" << packet_id
              << ",\"direction\":\"" << (downstream ? "to_sdk" : "to_px4")
              << "\",\"size\":" << packet.size() << ",\"reason\":\"" << reason
              << "\",\"framing_complete\":" << (framing.complete ? "true" : "false")
              << ",\"ids\":[";
    for (std::size_t index = 0; index < framing.ids.size(); ++index) {
        if (index) std::cout << ',';
        std::cout << framing.ids[index];
    }
    std::cout << "]}" << std::endl;
}

// Include overflow and malformed counters even when the parent keeps only a trace excerpt.
void stats(const lab::FaultEngine& engine, std::uint64_t now, std::uint64_t foreign) {
    const auto& count = engine.counters();
    std::cout << "{\"event\":\"stats\",\"at_ms\":" << now
              << ",\"received\":" << count.received << ",\"sent\":" << count.sent
              << ",\"dropped\":" << count.dropped << ",\"duplicated\":" << count.duplicated
              << ",\"reordered\":" << count.reordered << ",\"queue_drops\":" << count.queue_drops
              << ",\"malformed\":" << count.malformed << ",\"high_water\":" << count.high_water
              << ",\"foreign\":" << foreign << '}' << std::endl;
}
} // namespace

// Own the fixed socket and bounded control loop; watchdog or protocol/control failure exits nonzero.
int main(int argc, char**) {
    try {
        if (argc != 1) throw std::invalid_argument("This relay accepts no endpoint arguments");
        LoopbackSocket socket;
        lab::FaultEngine engine;
        const auto started = std::chrono::steady_clock::now();
        auto clock_ms = [&started]() {
            return static_cast<std::uint64_t>(std::chrono::duration_cast<std::chrono::milliseconds>(
                std::chrono::steady_clock::now() - started).count());
        };
        std::uint64_t foreign = 0, generation = 0;
        std::string input;
        bool running = true;
        std::cout << "{\"event\":\"ready\",\"at_ms\":0,\"simulation_only\":true}" << std::endl;
        while (running && clock_ms() < 900000) {
            pollfd descriptors[2]{{socket.fd, POLLIN, 0}, {STDIN_FILENO, POLLIN, 0}};
            if (poll(descriptors, 2, 5) < 0) throw std::runtime_error("Owned relay poll failed");
            const auto now = clock_ms();
            if (descriptors[1].revents & (POLLIN | POLLHUP)) {
                std::array<char, 256> buffer{};
                const auto size = read(STDIN_FILENO, buffer.data(), buffer.size());
                if (size <= 0) break;
                for (ssize_t index = 0; index < size; ++index) {
                    const auto byte = buffer[static_cast<std::size_t>(index)];
                    if (byte == '\n') {
                        if (input == "quit") { running = false; break; }
                        if (input == "stats") stats(engine, now, foreign);
                        else {
                            std::istringstream command(input);
                            std::string verb, profile, extra;
                            std::uint64_t duration = 0;
                            if (!(command >> verb >> profile >> duration) || verb != "profile" ||
                                (command >> extra)) throw std::invalid_argument("Invalid bounded control");
                            engine.configure(lab::parse_profile(profile), duration, now);
                            std::cout << "{\"event\":\"control\",\"at_ms\":" << now
                                      << ",\"generation\":" << ++generation << ",\"profile\":\""
                                      << lab::name(engine.current(now)) << "\"}" << std::endl;
                        }
                        input.clear();
                    } else {
                        if (input.size() >= 128 || byte < 32 || byte > 126)
                            throw std::invalid_argument("Control length/ASCII bound exceeded");
                        input += byte;
                    }
                }
            }
            if (descriptors[0].revents & POLLIN) {
                std::array<std::uint8_t, lab::max_packet + 1> buffer{};
                sockaddr_in peer{}; socklen_t length = sizeof(peer);
                const auto size = recvfrom(socket.fd, buffer.data(), buffer.size(), 0,
                                          reinterpret_cast<sockaddr*>(&peer), &length);
                if (size < 0) throw std::runtime_error("Owned relay receive failed");
                const auto port = ntohs(peer.sin_port);
                if (peer.sin_addr.s_addr != htonl(INADDR_LOOPBACK) || (port != 14580 && port != 14541)) {
                    ++foreign;
                } else {
                    const auto packet = std::span(buffer).first(static_cast<std::size_t>(size));
                    const auto reason = engine.receive(packet, port == 14580, now);
                    packet_event("receive", now, port == 14580, packet, reason, engine.counters().received);
                }
            }
            for (const auto& delivery : engine.due(now)) {
                auto target = LoopbackSocket::endpoint(delivery.to_sdk ? 14541 : 14580);
                const auto size = sendto(socket.fd, delivery.bytes.data(), delivery.bytes.size(), 0,
                                         reinterpret_cast<sockaddr*>(&target), sizeof(target));
                if (size != static_cast<ssize_t>(delivery.bytes.size()))
                    throw std::runtime_error("Owned relay send failed");
                packet_event("send", now, delivery.to_sdk, delivery.bytes, "delivery", delivery.packet_id);
            }
        }
        stats(engine, clock_ms(), foreign);
        return running ? 2 : 0; // A watchdog expiry is a failure, not successful acceptance.
    } catch (const std::exception& error) {
        std::cerr << "Simulator relay stopped: " << error.what() << '\n';
        return 1;
    }
}
