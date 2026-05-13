package com.youbuyfirst.backend.post;

import com.youbuyfirst.backend.instrument.Instrument;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

@Entity
@Table(name = "post_mentions")
public class PostMention {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "post_id", nullable = false)
    private CommunityPost post;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "instrument_id", nullable = false)
    private Instrument instrument;

    @Column(name = "matched_text", nullable = false, length = 200)
    private String matchedText;

    protected PostMention() {
    }

    public PostMention(CommunityPost post, Instrument instrument, String matchedText) {
        this.post = post;
        this.instrument = instrument;
        this.matchedText = matchedText;
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

    public String getMatchedText() {
        return matchedText;
    }
}

