package com.example.taskagent.task;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;

import java.time.LocalDate;
import java.time.OffsetDateTime;

import static org.assertj.core.api.Assertions.assertThat;

@DataJpaTest
class TaskJpaRepositoryTests {

    @Autowired
    private TaskJpaRepository taskJpaRepository;

    @Test
    void savePersistsTaskInDatabase() {
        OffsetDateTime now = OffsetDateTime.now();

        Task task = new Task();
        task.setTitle("Prepare weekly report");
        task.setDescription("Draft the weekly status update");
        task.setStatus(TaskStatus.TODO);
        task.setPriority(TaskPriority.HIGH);
        task.setDueDate(LocalDate.of(2026, 6, 17));
        task.setCreatedAt(now);
        task.setUpdatedAt(now);

        Task savedTask = taskJpaRepository.save(task);

        assertThat(savedTask.getId()).isNotNull();
        assertThat(taskJpaRepository.findById(savedTask.getId()))
                .hasValueSatisfying(foundTask -> {
                    assertThat(foundTask.getTitle()).isEqualTo("Prepare weekly report");
                    assertThat(foundTask.getStatus()).isEqualTo(TaskStatus.TODO);
                    assertThat(foundTask.getPriority()).isEqualTo(TaskPriority.HIGH);
                });
    }
}
