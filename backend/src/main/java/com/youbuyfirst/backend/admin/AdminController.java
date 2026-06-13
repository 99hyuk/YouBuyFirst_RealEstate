package com.youbuyfirst.backend.admin;

import com.youbuyfirst.backend.crawl.CrawlRunRepository;
import com.youbuyfirst.backend.crawl.CrawlTargetRepository;
import com.youbuyfirst.backend.crawl.dto.CrawlTargetView;
import com.youbuyfirst.backend.post.CommunityCommentCollectionTargetRepository;
import com.youbuyfirst.backend.post.CommunityPostDiffusionEventRepository;
import com.youbuyfirst.backend.post.CommunityPostRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/admin")
public class AdminController {

    private final CrawlRunRepository crawlRunRepository;
    private final CrawlTargetRepository crawlTargetRepository;
    private final CommunityPostRepository postRepository;
    private final CommunityPostDiffusionEventRepository diffusionEventRepository;
    private final CommunityCommentCollectionTargetRepository commentCollectionTargetRepository;

    public AdminController(
            CrawlRunRepository crawlRunRepository,
            CrawlTargetRepository crawlTargetRepository,
            CommunityPostRepository postRepository,
            CommunityPostDiffusionEventRepository diffusionEventRepository,
            CommunityCommentCollectionTargetRepository commentCollectionTargetRepository
    ) {
        this.crawlRunRepository = crawlRunRepository;
        this.crawlTargetRepository = crawlTargetRepository;
        this.postRepository = postRepository;
        this.diffusionEventRepository = diffusionEventRepository;
        this.commentCollectionTargetRepository = commentCollectionTargetRepository;
    }

    @GetMapping("/crawl-runs")
    public List<CrawlRunView> crawlRuns(@RequestParam(defaultValue = "20") int limit) {
        return crawlRunRepository.findByOrderByStartedAtDesc(PageRequest.of(0, clamp(limit))).stream()
                .map(CrawlRunView::from)
                .toList();
    }

    @GetMapping("/crawl-targets")
    public List<CrawlTargetView> crawlTargets(@RequestParam(defaultValue = "50") int limit) {
        return crawlTargetRepository.findByOrderByPriorityAscTargetIdAsc(PageRequest.of(0, clamp(limit))).stream()
                .map(CrawlTargetView::from)
                .toList();
    }

    @GetMapping("/posts")
    public List<PostView> posts(@RequestParam(required = false) String source, @RequestParam(defaultValue = "50") int limit) {
        if (source == null || source.isBlank()) {
            return postRepository.findByOrderByPublishedAtDesc(PageRequest.of(0, clamp(limit))).stream()
                    .map(PostView::from)
                    .toList();
        }
        return postRepository.findBySourceOrderByPublishedAtDesc(source.trim().toUpperCase(), PageRequest.of(0, clamp(limit))).stream()
                .map(PostView::from)
                .toList();
    }

    @GetMapping("/diffusion-events")
    @Transactional(readOnly = true)
    public List<PostDiffusionEventView> diffusionEvents(@RequestParam(required = false) String source, @RequestParam(defaultValue = "50") int limit) {
        if (source == null || source.isBlank()) {
            return diffusionEventRepository.findByOrderByObservedAtDesc(PageRequest.of(0, clamp(limit))).stream()
                    .map(PostDiffusionEventView::from)
                    .toList();
        }
        return diffusionEventRepository.findBySourceOrderByObservedAtDesc(source.trim().toUpperCase(), PageRequest.of(0, clamp(limit))).stream()
                .map(PostDiffusionEventView::from)
                .toList();
    }

    @GetMapping("/comment-collection-targets")
    @Transactional(readOnly = true)
    public List<CommentCollectionTargetView> commentCollectionTargets(@RequestParam(required = false) String source, @RequestParam(defaultValue = "50") int limit) {
        if (source == null || source.isBlank()) {
            return commentCollectionTargetRepository.findByOrderByPriorityAscCreatedAtAsc(PageRequest.of(0, clamp(limit))).stream()
                    .map(CommentCollectionTargetView::from)
                    .toList();
        }
        return commentCollectionTargetRepository.findBySourceOrderByPriorityAscCreatedAtAsc(source.trim().toUpperCase(), PageRequest.of(0, clamp(limit))).stream()
                .map(CommentCollectionTargetView::from)
                .toList();
    }

    private static int clamp(int limit) {
        return Math.max(1, Math.min(limit, 100));
    }
}
