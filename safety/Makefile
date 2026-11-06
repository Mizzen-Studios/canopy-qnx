# Compile only: output remains ignored, never committed. QNX qcc optional.
CC = cc
CFLAGS = -std=c11 -Wall -Wextra -Werror -pedantic -O2
OUT = ../build/safety
.PHONY: all clean
all: $(OUT)/safestop.o
$(OUT)/safestop.o: safestop.c safestop.h
	mkdir -p $(OUT)
	$(CC) $(CFLAGS) -c safestop.c -o $@
clean:
	$(RM) $(OUT)/safestop.o
