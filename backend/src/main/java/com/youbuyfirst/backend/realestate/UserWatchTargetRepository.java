package com.youbuyfirst.backend.realestate;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface UserWatchTargetRepository extends JpaRepository<UserWatchTarget, String> {

    List<UserWatchTarget> findByUserIdOrderByUpdatedAtDescCreatedAtDesc(String userId);

    Optional<UserWatchTarget> findByUserIdAndTargetTypeAndTargetId(String userId, String targetType, String targetId);

    void deleteByUserIdAndTargetTypeAndTargetId(String userId, String targetType, String targetId);
}
