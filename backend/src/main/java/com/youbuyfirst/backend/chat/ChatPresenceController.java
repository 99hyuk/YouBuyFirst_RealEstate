package com.youbuyfirst.backend.chat;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpSession;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/chat")
public class ChatPresenceController {

    private final ChatPresenceCounter counter;

    public ChatPresenceController(ChatPresenceCounter counter) {
        this.counter = counter;
    }

    @GetMapping("/presence")
    public ChatPresenceResponse presence(HttpServletRequest request) {
        HttpSession session = request.getSession(true);
        return new ChatPresenceResponse(counter.markPresent(session.getId()), "chat_presence_heartbeat");
    }
}
