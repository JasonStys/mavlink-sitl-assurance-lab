// Jason Stys: independent fault/framing oracles, seeded malformed corpus and throughput observation. Map: docs/SOURCE_MAP.md.
#include "fault.hpp"
#include <chrono>
#include <iostream>
#include <random>
#include <stdexcept>

// Unlike assert(), this oracle remains active in Release/NDEBUG builds.
void check(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

// Independently construct a length-consistent v2 header; CRC is deliberately not claimed valid.
std::vector<std::uint8_t> frame(std::uint32_t id, bool signed_frame = false) {
    std::vector<std::uint8_t> bytes(signed_frame ? 25 : 12, 0);
    bytes[0] = 0xfd; bytes[2] = signed_frame ? 1 : 0;
    bytes[7] = static_cast<std::uint8_t>(id & 255);
    bytes[8] = static_cast<std::uint8_t>((id >> 8) & 255);
    bytes[9] = static_cast<std::uint8_t>((id >> 16) & 255);
    return bytes;
}

// Run independent policy oracles and report an observational benchmark; never suppress a failure.
int main() {
    try {
        check(!lab::inspect({}).complete, "empty framing accepted");
        auto bytes = frame(123456, true);
        check(lab::inspect(bytes).ids.at(0) == 123456, "24-bit message ID/signing length");
        for (std::size_t size = 0; size < bytes.size(); ++size)
            check(!lab::inspect(std::span(bytes).first(size)).complete, "truncated frame accepted");
        auto heartbeat = frame(0);
        auto combined = heartbeat; combined.insert(combined.end(), bytes.begin(), bytes.end());
        check(lab::inspect(combined).ids.size() == 2, "concatenated frames lost");
        std::vector<std::uint8_t> v1{0xfe, 0, 0, 1, 1, 47, 0, 0};
        check(lab::inspect(v1).ids.at(0) == 47, "v1 message ID");
        bytes[2] = 2;
        check(!lab::inspect(bytes).complete, "unknown incompatible flag accepted");
        lab::FaultEngine engine;
        engine.configure(lab::Profile::delay, 1000, 0);
        engine.receive(heartbeat, true, 0);
        check(engine.due(249).empty(), "delay released too early");
        check(engine.due(250).at(0).bytes == heartbeat, "delay mutated bytes");
        engine.configure(lab::Profile::duplicate, 1000, 1000);
        engine.receive(heartbeat, true, 1001);
        check(engine.due(1001).size() == 2, "duplicate count");
        engine.configure(lab::Profile::reorder, 1000, 2000);
        engine.receive(heartbeat, true, 2000);
        auto ack = frame(47); engine.receive(ack, true, 2001);
        auto reversed = engine.due(2001);
        check(reversed.at(0).bytes == ack && reversed.at(1).bytes == heartbeat, "pair order");
        engine.receive(heartbeat, false, 2002);
        check(engine.due(2102).size() == 1, "unpaired packet stuck");
        engine.configure(lab::Profile::ack_loss, 1000, 3000);
        check(engine.receive(ack, true, 3000) == "drop_ack", "downstream ACK not lost");
        engine.receive(ack, false, 3000);
        check(engine.due(3000).size() == 1, "upstream ACK incorrectly lost");
        engine.configure(lab::Profile::blackout, 1000, 4000);
        engine.receive(heartbeat, false, 4001);
        check(engine.due(4001).empty(), "blackout leak");
        engine.receive(heartbeat, true, 5000);
        check(engine.due(5000).size() == 1, "expiry boundary did not recover");
        engine.configure(lab::Profile::delay, 1000, 6000);
        for (int index = 0; index < 1000; ++index) engine.receive(heartbeat, true, 6000);
        check(engine.counters().high_water == lab::max_pending, "queue not bounded");
        check(engine.counters().queue_drops > 0, "queue overflow not counted");
        engine.configure(lab::Profile::normal, 0, 6001);
        check(engine.due(9999).empty(), "profile change leaked queued bytes");
        bool rejected = false;
        try { engine.configure(lab::Profile::normal, 60001, 0); }
        catch (const std::invalid_argument&) { rejected = true; }
        check(rejected, "unbounded duration accepted");
        rejected = false;
        try { (void)lab::parse_profile("remote-radio"); }
        catch (const std::invalid_argument&) { rejected = true; }
        check(rejected, "unknown profile accepted");
        std::mt19937 random(42);
        for (int index = 0; index < 20000; ++index) {
            std::vector<std::uint8_t> malformed(random() % 300);
            for (auto& byte : malformed) byte = static_cast<std::uint8_t>(random() & 255);
            (void)lab::inspect(malformed);
        }
        auto start = std::chrono::steady_clock::now();
        for (std::uint64_t index = 0; index < 50000; ++index) {
            engine.receive(heartbeat, true, index + 10000);
            check(engine.due(index + 10000).size() == 1, "throughput observation lost packet");
        }
        const auto elapsed = std::chrono::duration_cast<std::chrono::microseconds>(
            std::chrono::steady_clock::now() - start).count();
        std::cout << "CORE_ACCEPTANCE {\"seed\":42,\"malformed_cases\":20000,"
                  << "\"measured_packets\":50000,\"elapsed_us\":" << elapsed
                  << ",\"queue_limit\":256,\"all_oracles_passed\":true}\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Independent oracle failed: " << error.what() << '\n';
        return 1;
    }
}
