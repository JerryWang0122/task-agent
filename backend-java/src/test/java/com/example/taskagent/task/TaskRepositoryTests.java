package com.example.taskagent.task;

import org.junit.jupiter.api.Test;

import java.time.LocalDate;

import static org.assertj.core.api.Assertions.assertThat;

class TaskRepositoryTests {

    @Test
    void saveAssignsIdAndTimestamps() {
        TaskRepository repository = new TaskRepository();

        Task task = new Task();
        task.setTitle("Prepare weekly report");
        task.setStatus(TaskStatus.TODO);
        task.setPriority(TaskPriority.HIGH);
        task.setDueDate(LocalDate.now());

        Task savedTask = repository.save(task);

        assertThat(savedTask.getId()).isEqualTo(1L);
        assertThat(savedTask.getCreatedAt()).isNotNull();
        assertThat(savedTask.getUpdatedAt()).isNotNull();
        assertThat(repository.findAll()).containsExactly(savedTask);
    }

    @Test
    void findByIdReturnsTaskWhenItExists() {
        TaskRepository repository = new TaskRepository();

        Task task = new Task();
        task.setTitle("Read MCP documentation");
        task.setStatus(TaskStatus.TODO);
        task.setPriority(TaskPriority.MEDIUM);

        Task savedTask = repository.save(task);

        assertThat(repository.findById(savedTask.getId())).contains(savedTask);
    }

    @Test
    void deleteByIdRemovesTask() {
        TaskRepository repository = new TaskRepository();

        Task task = new Task();
        task.setTitle("Clean completed tasks");
        task.setStatus(TaskStatus.TODO);
        task.setPriority(TaskPriority.LOW);

        Task savedTask = repository.save(task);

        boolean deleted = repository.deleteById(savedTask.getId());

        assertThat(deleted).isTrue();
        assertThat(repository.findById(savedTask.getId())).isEmpty();
    }
}
