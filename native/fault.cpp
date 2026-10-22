// Jason Stys: length-safe framing and bounded, byte-preserving fault policy. Symbols: docs/SOURCE_MAP.md.
#include "fault.hpp"
#include <algorithm>
#include <limits>
#include <stdexcept>

namespace lab {
// Walk complete concatenated v1/v2 frames, including v2 signing trailers; never read unchecked offsets.
Framing inspect(std::span<const std::uint8_t> bytes) {
    Framing result;
    if (bytes.empty() || bytes.size() > max_packet) return result;
    std::size_t offset = 0;
    while (offset < bytes.size()) {
        const auto rest = bytes.subspan(offset);
        if (rest.size() < 2) return result;
        const bool v2 = rest[0] == 0xfd;
        if (!v2 && rest[0] != 0xfe) return result;
        const std::size_t header = v2 ? 10 : 6;
        if (rest.size() < header) return result;
        if (v2 && (rest[2] & 0xfe) != 0) return result;
        const std::size_t length = header + rest[1] + 2 + (v2 && (rest[2] & 1) ? 13 : 0);
        if (rest.size() < length) return result;
        result.ids.push_back(v2 ? static_cast<std::uint32_t>(rest[7]) |
                                     (static_cast<std::uint32_t>(rest[8]) << 8) |
                                     (static_cast<std::uint32_t>(rest[9]) << 16)
                               : rest[5]);
        offset += length;
    }
    result.complete = true;
    return result;
}

// Fixed names form the complete control vocabulary; no expression/plugin/command execution.
std::string name(Profile profile) {
    switch (profile) {
        case Profile::normal: return "normal";
        case Profile::blackout: return "blackout";
        case Profile::delay: return "delay";
        case Profile::reorder: return "reorder";
        case Profile::duplicate: return "duplicate";
        case Profile::ack_loss: return "ack_loss";
    }
    throw std::invalid_argument("Unknown profile");
}

Profile parse_profile(const std::string& value) {
    for (auto profile : {Profile::normal, Profile::blackout, Profile::delay,
                         Profile::reorder, Profile::duplicate, Profile::ack_loss}) {
        if (name(profile) == value) return profile;
    }
    throw std::invalid_argument("Unsupported profile");
}

// Profile changes purge queued datagrams: stale command bytes are never released by a later profile.
void FaultEngine::configure(Profile profile, std::uint64_t duration_ms, std::uint64_t now_ms) {
    if (duration_ms > 60000 || now_ms > std::numeric_limits<std::uint64_t>::max() - duration_ms)
        throw std::invalid_argument("Fault duration is outside the 60 second budget");
    counters_.dropped += pending_.size();
    pending_.clear();
    profile_ = profile;
    expires_ = now_ms + duration_ms;
}

Profile FaultEngine::current(std::uint64_t now_ms) const {
    return now_ms < expires_ ? profile_ : Profile::normal;
}

// At most 256 * 2048 bytes plus bounded container overhead can await delivery.
void FaultEngine::enqueue(Delivery delivery) {
    if (pending_.size() >= max_pending) {
        ++counters_.queue_drops;
        ++counters_.dropped;
        return;
    }
    pending_.push_back(std::move(delivery));
    counters_.high_water = std::max(counters_.high_water, pending_.size());
}

// Never mutate datagram bytes. Framing metadata only selects mission ACK loss (ID 47).
std::string FaultEngine::receive(std::span<const std::uint8_t> packet, bool to_sdk,
                                 std::uint64_t now_ms) {
    if (now_ms > std::numeric_limits<std::uint64_t>::max() - 250)
        throw std::invalid_argument("Monotonic timer overflow");
    ++counters_.received;
    const auto framing = inspect(packet);
    if (!framing.complete) ++counters_.malformed;
    const auto profile = current(now_ms);
    if (packet.empty() || packet.size() > max_packet || profile == Profile::blackout ||
        (profile == Profile::ack_loss && to_sdk &&
         std::find(framing.ids.begin(), framing.ids.end(), 47u) != framing.ids.end())) {
        ++counters_.dropped;
        return profile == Profile::ack_loss ? "drop_ack" : "drop";
    }
    Delivery delivery{{packet.begin(), packet.end()}, to_sdk, now_ms, counters_.received};
    if (profile == Profile::delay) delivery.due_ms += 250;
    if (profile == Profile::reorder) {
        auto held = std::find_if(pending_.begin(), pending_.end(), [to_sdk](const auto& item) {
            return item.to_sdk == to_sdk;
        });
        if (held != pending_.end()) {
            auto older = std::move(*held);
            pending_.erase(held);
            older.due_ms = now_ms;
            enqueue(std::move(delivery));
            enqueue(std::move(older));
            ++counters_.reordered;
            return "reorder_pair";
        }
        delivery.due_ms += 100; // An unpaired final datagram is never held indefinitely.
    }
    enqueue(delivery);
    if (profile == Profile::duplicate) {
        enqueue(std::move(delivery));
        ++counters_.duplicated;
        return "duplicate";
    }
    return profile == Profile::delay ? "delay" : "forward";
}

// O(Q) with a hard Q <= 256, preserving insertion order among currently due packets.
std::vector<Delivery> FaultEngine::due(std::uint64_t now_ms) {
    std::vector<Delivery> output;
    std::deque<Delivery> waiting;
    for (auto& item : pending_) {
        if (item.due_ms <= now_ms) {
            output.push_back(std::move(item));
            ++counters_.sent;
        } else waiting.push_back(std::move(item));
    }
    pending_.swap(waiting);
    return output;
}
} // namespace lab
