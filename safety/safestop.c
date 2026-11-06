/* Authored from CANopy app protocol and FSM specification, not SDK source. */
#include "safestop.h"
#include <math.h>
void canopy_safestop_init(struct canopy_safestop *s)
{
    *s = (struct canopy_safestop){ .latched = true, .brake = 100 };
}
bool canopy_safestop_cycle(struct canopy_safestop *s, uint64_t now,
                          const struct canopy_inputs *in, struct canopy_heartbeat *out)
{
    bool healthy;
    unsigned state;
    if (!s || !in || !out || (s->has_time && now <= s->last_ms)) return false;
    healthy = !(s->has_time && now - s->last_ms > 20) &&
        in->speed_age_ms >= 0 && in->speed_age_ms <= 30 &&
        in->obstacle_age_ms >= 0 && in->obstacle_age_ms <= 30 &&
        isfinite(in->obstacle_m) && in->obstacle_m > 5 &&
        isfinite(in->pilot_speed_mps) && in->pilot_speed_mps >= 0 &&
        in->pilot_speed_mps <= 20;
    s->last_ms = now;
    s->has_time = true;
    if (!healthy) {
        s->latched = true;
        s->fresh_cycles = 0;
        s->brake = 100;
    } else if (s->latched) {
        if (++s->fresh_cycles >= 10) s->latched = false;
    }
    /* Saturate bookkeeping, avoiding wrap in a long-running C adapter. */
    if (!s->latched && s->fresh_cycles >= 10 && s->fresh_cycles < 12)
        ++s->fresh_cycles;
    if (s->latched || (s->fresh_cycles == 11 && s->brake == 100))
        state = CANOPY_SAFE_STOP;
    else if (s->brake) {
        state = CANOPY_RECOVER;
        s->brake = s->brake > 10 ? s->brake - 10 : 0;
    } else state = CANOPY_DRIVE;
    *out = (struct canopy_heartbeat){ state, s->brake, s->counter };
    s->counter = (s->counter + 1) & 15;
    return true;
}
uint8_t canopy_crc8(const uint8_t *data, size_t size)
{
    uint8_t crc = 0xff;
    size_t i;
    unsigned bit;
    for (i = 0; i < size; ++i) {
        crc ^= data[i];
        for (bit = 0; bit < 8; ++bit)
            crc = (uint8_t)((crc << 1) ^ ((crc & 0x80) ? 0x1d : 0));
    }
    return (uint8_t)(crc ^ 0xff);
}
bool canopy_heartbeat_encode(const struct canopy_heartbeat *p, uint8_t out[4])
{
    uint8_t body[5];
    if (!p || !out || p->state > CANOPY_RECOVER || p->brake > 100 ||
        p->counter > 15 || (p->state == CANOPY_SAFE_STOP && p->brake != 100))
        return false;
    body[0] = 2; body[1] = 0;
    body[2] = (uint8_t)p->state;
    body[3] = (uint8_t)p->brake;
    body[4] = (uint8_t)p->counter;
    out[0] = body[2]; out[1] = body[3]; out[2] = body[4];
    out[3] = canopy_crc8(body, sizeof(body));
    return true;
}
bool canopy_heartbeat_decode(uint32_t id, const uint8_t *data, size_t size,
                             struct canopy_heartbeat *out)
{
    struct canopy_heartbeat p;
    uint8_t encoded[4];
    if (!data || !out || id != CANOPY_HEARTBEAT_ID || size != 4) return false;
    p = (struct canopy_heartbeat){ data[0], data[1], data[2] };
    if (!canopy_heartbeat_encode(&p, encoded) || encoded[3] != data[3]) return false;
    *out = p;
    return true;
}
