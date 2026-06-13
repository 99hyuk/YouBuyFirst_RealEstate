package com.youbuyfirst.backend.realestate;

import org.springframework.data.jpa.repository.JpaRepository;

public interface PolicyEventTargetRepository extends JpaRepository<PolicyEventTarget, PolicyEventTargetId> {
}
