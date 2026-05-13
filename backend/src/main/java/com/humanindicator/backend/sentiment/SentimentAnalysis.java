package com.humanindicator.backend.sentiment;

import com.humanindicator.backend.instrument.Instrument;
import com.humanindicator.backend.post.CommunityPost;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "sentiment_analyses")
public class SentimentAnalysis {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "post_id", nullable = false)
    private CommunityPost post;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "instrument_id", nullable = false)
    private Instrument instrument;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private SentimentLabel sentiment;

    @Column(nullable = false)
    private double confidence;

    @Column(length = 500)
    private String rationale;

    @Column(length = 100)
    private String model;

    @Column(name = "analyzed_at", nullable = false)
    private Instant analyzedAt;

    protected SentimentAnalysis() {
    }

    public SentimentAnalysis(CommunityPost post, Instrument instrument, SentimentLabel sentiment, double confidence, String rationale, String model, Instant analyzedAt) {
        this.post = post;
        this.instrument = instrument;
        this.sentiment = sentiment;
        this.confidence = confidence;
        this.rationale = rationale;
        this.model = model;
        this.analyzedAt = analyzedAt;
    }

    public Long getId() {
        return id;
    }

    public CommunityPost getPost() {
        return post;
    }

    public Instrument getInstrument() {
        return instrument;
    }

    public SentimentLabel getSentiment() {
        return sentiment;
    }

    public double getConfidence() {
        return confidence;
    }

    public String getRationale() {
        return rationale;
    }

    public String getModel() {
        return model;
    }

    public Instant getAnalyzedAt() {
        return analyzedAt;
    }
}

