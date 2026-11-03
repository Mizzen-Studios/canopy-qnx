# Offline replay design

Palette follows plan v3: background #181c1e, panels #232729/#2c3032,
ink #fbf8f4, quiet ink #c0c0bb, teal #2ec4a6, warning #ffb020,
coral #ff443a only on stop/fault, violet #8c62ff for playback.
System sans-serif for controls; system monospace for logical time and records.
No web fonts or requests. Left aligned instrumentation, not marketing cards.

1920x1080 composition:

    identity + permanent HOST SIMULATION / NOT QNX warning
    replay transport / local file / logical-time scrubber
    A vehicle schematic + state     C modeled inputs / explicit unavailable
    B raw host record               D transport availability strip
    E full-width logical-time watchdog band

The memorable element is a road-line vehicle schematic that changes brake and
hazard indicators, not fabricated telemetry. A-E mirror the planned dashboard
without imitating QNX evidence. B is a host JSON record, never a ttyd shell.
C shows only fields actually available; ages/obstacle/pilot are unavailable.
D explicitly says SSH, PIDs, driver stats and live CAN are not recorded.
E plots watchdog states from the replay, never measured restart durations.

Review against brief: retain the prescribed dark instrument palette; reject
live-looking terminal and healthy ETH/SSH badges because those would imply
unavailable evidence. Keep the unavailable areas visible instead of making up
values. Four primary signals maximum. Stack on mobile, keyboard-visible focus,
manual playback only, no network/server dependency.
