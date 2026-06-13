package com.youbuyfirst.backend.realestate;

import java.io.Serializable;
import java.util.Objects;

public class PolicyEventTargetId implements Serializable {

    private String policyEventId;
    private String targetId;
    private String impactType;

    public PolicyEventTargetId() {
    }

    public PolicyEventTargetId(String policyEventId, String targetId, String impactType) {
        this.policyEventId = policyEventId;
        this.targetId = targetId;
        this.impactType = impactType;
    }

    @Override
    public boolean equals(Object other) {
        if (this == other) {
            return true;
        }
        if (!(other instanceof PolicyEventTargetId that)) {
            return false;
        }
        return Objects.equals(policyEventId, that.policyEventId)
                && Objects.equals(targetId, that.targetId)
                && Objects.equals(impactType, that.impactType);
    }

    @Override
    public int hashCode() {
        return Objects.hash(policyEventId, targetId, impactType);
    }
}
