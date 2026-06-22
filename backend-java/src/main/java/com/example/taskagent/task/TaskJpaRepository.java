package com.example.taskagent.task;

import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.LocalDate;
import java.util.List;

public interface TaskJpaRepository extends JpaRepository<Task, Long> {
    List<Task> findByDueDateBeforeAndStatusNot(LocalDate dueDate, TaskStatus status, Sort sort);
}
