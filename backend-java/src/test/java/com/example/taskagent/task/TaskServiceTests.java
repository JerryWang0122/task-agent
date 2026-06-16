package com.example.taskagent.task;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class TaskServiceTests {

    @Test
    void createTaskAppliesDefaultStatusAndPriority() {
        TaskService service = new TaskService(new TaskRepository());

        Task task = new Task();
        task.setTitle("Review Spring Boot API design");

        Task createdTask = service.createTask(task);

        assertThat(createdTask.getId()).isEqualTo(1L);
        assertThat(createdTask.getStatus()).isEqualTo(TaskStatus.TODO);
        assertThat(createdTask.getPriority()).isEqualTo(TaskPriority.MEDIUM);
    }

    @Test
    void completeTaskMarksExistingTaskAsDone() {
        TaskService service = new TaskService(new TaskRepository());

        Task task = new Task();
        task.setTitle("Pay electricity bill");
        Task createdTask = service.createTask(task);

        assertThat(service.completeTask(createdTask.getId()))
                .hasValueSatisfying(completedTask -> assertThat(completedTask.getStatus()).isEqualTo(TaskStatus.DONE));
    }

    @Test
    void completeTaskReturnsEmptyWhenTaskDoesNotExist() {
        TaskService service = new TaskService(new TaskRepository());

        assertThat(service.completeTask(999L)).isEmpty();
    }

    @Test
    void listTasksReturnsCreatedTasks() {
        TaskService service = new TaskService(new TaskRepository());

        Task firstTask = new Task();
        firstTask.setTitle("Prepare weekly report");
        Task secondTask = new Task();
        secondTask.setTitle("Read MCP documentation");

        Task createdFirstTask = service.createTask(firstTask);
        Task createdSecondTask = service.createTask(secondTask);

        assertThat(service.listTasks()).containsExactly(createdFirstTask, createdSecondTask);
    }
}
