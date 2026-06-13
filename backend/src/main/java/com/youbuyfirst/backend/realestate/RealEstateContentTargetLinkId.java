package com.youbuyfirst.backend.realestate;

import java.io.Serializable;
import java.util.Objects;

public class RealEstateContentTargetLinkId implements Serializable {

    private String contentItemId;
    private String targetId;
    private String linkType;

    protected RealEstateContentTargetLinkId() {
    }

    public RealEstateContentTargetLinkId(String contentItemId, String targetId, String linkType) {
        this.contentItemId = contentItemId;
        this.targetId = targetId;
        this.linkType = linkType;
    }

    public String getContentItemId() {
        return contentItemId;
    }

    public String getTargetId() {
        return targetId;
    }

    public String getLinkType() {
        return linkType;
    }

    @Override
    public boolean equals(Object other) {
        if (this == other) {
            return true;
        }
        if (!(other instanceof RealEstateContentTargetLinkId that)) {
            return false;
        }
        return Objects.equals(contentItemId, that.contentItemId)
                && Objects.equals(targetId, that.targetId)
                && Objects.equals(linkType, that.linkType);
    }

    @Override
    public int hashCode() {
        return Objects.hash(contentItemId, targetId, linkType);
    }
}
