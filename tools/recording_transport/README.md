# Recording-only shell transport

Additive HOST-tested helper, not frozen product or native acceptance. Eight-byte octal chunks, nonce/sequence standalone acknowledgments constructed separately from command echoes, no retry; size and SHA256 from existing guest toybox applets must match before caller may execute. Missing applet/ack/integrity fails closed. Existing IFS contains toybox/hash usage strings; actual applet availability remains a native gate, never assumed from HOST tests.

Private callers retain exact host-write and received spans with monotonic timestamps. No payload execution in this helper. Tests use a real HOST PTY and shell, byte-exact controls/quotes/newlines, truncation, lost ack/echo impostor, corruption, timeout and delayed backpressure. Run `python3 -m unittest discover -s tests/recording_transport -v`. These are HOST tests, not QNX tests.
