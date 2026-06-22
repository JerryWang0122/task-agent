package com.example.taskagent.task;

import com.example.taskagent.task.dto.CreateTaskRequest;
import com.example.taskagent.task.dto.TaskResponse;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDate;
import java.util.List;

@RestController
@RequestMapping("/api/tasks")
public class TaskController {

    private final TaskService taskService;

    public TaskController(TaskService taskService) {
        this.taskService = taskService;
    }

    @GetMapping
    public List<TaskResponse> listTasks() {
        return taskService.listTasks().stream()
                .map(TaskResponse::from)
                .toList();
    }

    @GetMapping("/overdue")
    public List<TaskResponse> findOverdueTasks() {
        return taskService.findOverdueTasks(LocalDate.now()).stream()
                .map(TaskResponse::from)
                .toList();
    }

    @GetMapping("/{id}")
    public ResponseEntity<TaskResponse> getTask(@PathVariable Long id) {
        return taskService.getTask(id)
                .map(TaskResponse::from)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    @PostMapping
    public ResponseEntity<TaskResponse> createTask(@RequestBody CreateTaskRequest request) {
        Task task = new Task();
        task.setTitle(request.getTitle());
        task.setDescription(request.getDescription());
        task.setPriority(request.getPriority());
        task.setDueDate(request.getDueDate());

        Task createdTask = taskService.createTask(task);

        return ResponseEntity.status(HttpStatus.CREATED).body(TaskResponse.from(createdTask));
    }

    @PatchMapping("/{id}/complete")
    public ResponseEntity<TaskResponse> completeTask(@PathVariable Long id) {
        return taskService.completeTask(id)
                .map(TaskResponse::from)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteTask(@PathVariable Long id) {
        if (taskService.deleteTask(id)) {
            return ResponseEntity.noContent().build();
        }

        return ResponseEntity.notFound().build();
    }
}
