package com.youbuyfirst.backend.chat;

import com.youbuyfirst.backend.chat.dto.ChatNicknameAvailabilityResponse;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/chat")
public class ChatNicknameController {

    private final ChatMessageService service;

    public ChatNicknameController(ChatMessageService service) {
        this.service = service;
    }

    @GetMapping("/nickname-availability")
    public ChatNicknameAvailabilityResponse nicknameAvailability(@RequestParam String displayName) {
        return service.nicknameAvailability(displayName);
    }
}
