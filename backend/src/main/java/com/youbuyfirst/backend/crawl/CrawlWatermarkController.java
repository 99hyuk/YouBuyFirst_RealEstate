package com.youbuyfirst.backend.crawl;

import com.youbuyfirst.backend.crawl.dto.CrawlWatermarkResponse;
import com.youbuyfirst.backend.post.CommunityPost;
import com.youbuyfirst.backend.post.CommunityPostRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/internal/crawl-watermarks")
public class CrawlWatermarkController {

    private final CommunityPostRepository postRepository;

    public CrawlWatermarkController(CommunityPostRepository postRepository) {
        this.postRepository = postRepository;
    }

    @GetMapping
    public ResponseEntity<CrawlWatermarkResponse> latest(
            @RequestParam String source,
            @RequestParam String boardId
    ) {
        return postRepository.findFirstBySourceAndBoardIdOrderByPublishedAtDescCrawledAtDesc(
                        source.trim().toUpperCase(),
                        boardId.trim()
                )
                .map(this::toResponse)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.noContent().build());
    }

    private CrawlWatermarkResponse toResponse(CommunityPost post) {
        return new CrawlWatermarkResponse(
                post.getSource(),
                post.getBoardId(),
                post.getExternalId(),
                post.getPublishedAt()
        );
    }
}
