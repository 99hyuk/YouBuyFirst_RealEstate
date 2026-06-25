package com.youbuyfirst.backend.chat;

import org.junit.jupiter.api.Test;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneId;

import static org.assertj.core.api.Assertions.assertThat;

class ChatPresenceCounterTest {

    @Test
    void countsOnlyChatSessionsSeenWithinTheHeartbeatWindow() {
        MutableClock clock = new MutableClock(Instant.parse("2026-06-25T00:00:00Z"));
        ChatPresenceCounter counter = new ChatPresenceCounter(clock, Duration.ofSeconds(45));

        assertThat(counter.markPresent("session-a")).isEqualTo(1);

        clock.advance(Duration.ofSeconds(20));
        assertThat(counter.markPresent("session-b")).isEqualTo(2);

        clock.advance(Duration.ofSeconds(26));
        assertThat(counter.activeChatSessionCount()).isEqualTo(1);
    }

    private static final class MutableClock extends Clock {

        private Instant instant;

        private MutableClock(Instant instant) {
            this.instant = instant;
        }

        @Override
        public ZoneId getZone() {
            return ZoneId.of("UTC");
        }

        @Override
        public Clock withZone(ZoneId zone) {
            return Clock.fixed(instant, zone);
        }

        @Override
        public Instant instant() {
            return instant;
        }

        private void advance(Duration duration) {
            instant = instant.plus(duration);
        }
    }
}
