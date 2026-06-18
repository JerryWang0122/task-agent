package com.example.taskagent.task;

import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.util.List;

@Component
public class TaskDataSeeder implements CommandLineRunner {

    private final TaskJpaRepository taskRepository;

    public TaskDataSeeder(TaskJpaRepository taskRepository) {
        this.taskRepository = taskRepository;
    }

    @Override
    public void run(String... args) {
        if (taskRepository.count() > 0) {
            return;
        }

        LocalDate today = LocalDate.now();
        OffsetDateTime now = OffsetDateTime.now();

        taskRepository.saveAll(List.of(
                task(
                        "Review Spring Boot persistence notes",
                        "Connect the REST API to H2 through Spring Data JPA.",
                        TaskStatus.TODO,
                        TaskPriority.HIGH,
                        today,
                        now
                ),
                task(
                        "Prepare weekly report",
                        "Summarize project progress and blockers.",
                        TaskStatus.IN_PROGRESS,
                        TaskPriority.MEDIUM,
                        today.plusDays(2),
                        now
                ),
                task(
                        "Clean up overdue admin task",
                        "Use this sample to test overdue task queries later.",
                        TaskStatus.TODO,
                        TaskPriority.URGENT,
                        today.minusDays(1),
                        now
                ),
                task(
                        "Archive completed tutorial notes",
                        "A completed sample task for status filtering.",
                        TaskStatus.DONE,
                        TaskPriority.LOW,
                        today.minusDays(2),
                        now
                )
        ));
    }

    private Task task(
            String title,
            String description,
            TaskStatus status,
            TaskPriority priority,
            LocalDate dueDate,
            OffsetDateTime timestamp
    ) {
        Task task = new Task();
        task.setTitle(title);
        task.setDescription(description);
        task.setStatus(status);
        task.setPriority(priority);
        task.setDueDate(dueDate);
        task.setCreatedAt(timestamp);
        task.setUpdatedAt(timestamp);
        return task;
    }
}
