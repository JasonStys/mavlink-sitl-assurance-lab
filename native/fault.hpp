// Jason Stys: bounded packet framing and deterministic fault policy. Declarations/variables: docs/SOURCE_MAP.md.
#pragma once
#include <cstdint>
#include <deque>
#include <span>
#include <string>
#include <vector>

namespace lab {
constexpr std::size_t max_packet = 2048;
constexpr std::size_t max_pending = 256;

// Header/length inspection only. These fields do NOT prove CRC validity, identity or signing.
struct Framing {
    bool complete = false;
    std::vector<std::uint32_t> ids;
};
Framing inspect(std::span<const std::uint8_t> bytes);

enum class Profile { normal, blackout, delay, reorder, duplicate, ack_loss };
std::string name(Profile profile);
Profile parse_profile(const std::string& value);

// One opaque datagram and its fixed direction: true sends to SDK, false to owned PX4.
struct Delivery {
    std::vector<std::uint8_t> bytes;
    bool to_sdk = true;
    std::uint64_t due_ms = 0;
    std::uint64_t packet_id = 0;
};

// Cumulative counters are independent of the bounded trace excerpt retained by Python.
struct Counters {
    std::uint64_t received = 0, sent = 0, dropped = 0, duplicated = 0, reordered = 0;
    std::uint64_t queue_drops = 0, malformed = 0;
    std::size_t high_water = 0;
};

// No sockets, clocks, sleeps or global state: callers supply monotonic milliseconds.
class FaultEngine {
  public:
    void configure(Profile profile, std::uint64_t duration_ms, std::uint64_t now_ms);
    std::string receive(std::span<const std::uint8_t> packet, bool to_sdk, std::uint64_t now_ms);
    std::vector<Delivery> due(std::uint64_t now_ms);
    Profile current(std::uint64_t now_ms) const;
    // Immutable policy counts; scheduled sends are not proof of peer delivery.
    const Counters& counters() const { return counters_; }
  private:
    void enqueue(Delivery delivery);
    Profile profile_ = Profile::normal;
    std::uint64_t expires_ = 0;
    std::deque<Delivery> pending_;
    Counters counters_;
};
} // namespace lab
