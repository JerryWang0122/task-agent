package com.example.taskagent.task;

import org.junit.jupiter.api.Test;
import org.springframework.data.domain.Sort;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class TaskServiceTests {

    @Test
    void createTaskAppliesDefaultStatusAndPriority() {
        TaskJpaRepository repository = mock(TaskJpaRepository.class);
        TaskService service = new TaskService(repository);

        Task task = new Task();
        task.setTitle("Review Spring Boot API design");
        when(repository.save(any(Task.class))).thenAnswer(invocation -> {
            Task savedTask = invocation.getArgument(0);
            savedTask.setId(1L);
            return savedTask;
        });

        Task createdTask = service.createTask(task);

        assertThat(createdTask.getId()).isEqualTo(1L);
        assertThat(createdTask.getStatus()).isEqualTo(TaskStatus.TODO);
        assertThat(createdTask.getPriority()).isEqualTo(TaskPriority.MEDIUM);
        assertThat(createdTask.getCreatedAt()).isNotNull();
        assertThat(createdTask.getUpdatedAt()).isNotNull();
    }

    @Test
    void completeTaskMarksExistingTaskAsDone() {
        TaskJpaRepository repository = mock(TaskJpaRepository.class);
        TaskService service = new TaskService(repository);

        Task task = new Task();
        task.setId(1L);
        task.setTitle("Pay electricity bill");
        task.setStatus(TaskStatus.TODO);
        task.setPriority(TaskPriority.MEDIUM);
        when(repository.findById(1L)).thenReturn(Optional.of(task));
        when(repository.save(any(Task.class))).thenAnswer(invocation -> invocation.getArgument(0));

        assertThat(service.completeTask(1L))
                .hasValueSatisfying(completedTask -> {
                    assertThat(completedTask.getStatus()).isEqualTo(TaskStatus.DONE);
                    assertThat(completedTask.getUpdatedAt()).isNotNull();
                });
    }

    @Test
    void completeTaskReturnsEmptyWhenTaskDoesNotExist() {
        TaskJpaRepository repository = mock(TaskJpaRepository.class);
        TaskService service = new TaskService(repository);
        when(repository.findById(999L)).thenReturn(Optional.empty());

        assertThat(service.completeTask(999L)).isEmpty();
    }

    @Test
    void listTasksReturnsCreatedTasks() {
        TaskJpaRepository repository = mock(TaskJpaRepository.class);
        TaskService service = new TaskService(repository);

        Task firstTask = new Task();
        firstTask.setId(1L);
        firstTask.setTitle("Prepare weekly report");
        Task secondTask = new Task();
        secondTask.setId(2L);
        secondTask.setTitle("Read MCP documentation");
        when(repository.findAll(Sort.by(Sort.Direction.ASC, "id")))
                .thenReturn(List.of(firstTask, secondTask));

        assertThat(service.listTasks()).containsExactly(firstTask, secondTask);
    }

    @Test
    void findOverdueTasksReturnsOpenTasksDueBeforeToday() {
        TaskJpaRepository repository = mock(TaskJpaRepository.class);
        TaskService service = new TaskService(repository);
        LocalDate today = LocalDate.of(2026, 6, 19);

        Task overdueTask = new Task();
        overdueTask.setId(1L);
        overdueTask.setTitle("Clean up overdue admin task");
        overdueTask.setStatus(TaskStatus.TODO);
        overdueTask.setDueDate(today.minusDays(1));

        when(repository.findByDueDateBeforeAndStatusNot(
                today,
                TaskStatus.DONE,
                Sort.by(Sort.Direction.ASC, "dueDate", "id")
        )).thenReturn(List.of(overdueTask));

        assertThat(service.findOverdueTasks(today)).containsExactly(overdueTask);
    }

    @Test
    void deleteTaskDeletesExistingTask() {
        TaskJpaRepository repository = mock(TaskJpaRepository.class);
        TaskService service = new TaskService(repository);
        when(repository.existsById(1L)).thenReturn(true);

        boolean deleted = service.deleteTask(1L);

        assertThat(deleted).isTrue();
        verify(repository).deleteById(1L);
    }
}
