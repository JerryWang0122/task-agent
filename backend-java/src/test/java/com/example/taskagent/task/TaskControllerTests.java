package com.example.taskagent.task;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Optional;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(TaskController.class)
class TaskControllerTests {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private TaskService taskService;

    @Test
    void listTasksReturnsTaskResponses() throws Exception {
        when(taskService.listTasks()).thenReturn(List.of(sampleTask(1L, "Prepare weekly report", TaskStatus.TODO)));

        mockMvc.perform(get("/api/tasks"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].id").value(1L))
                .andExpect(jsonPath("$[0].title").value("Prepare weekly report"))
                .andExpect(jsonPath("$[0].status").value("TODO"));
    }

    @Test
    void getTaskReturnsNotFoundWhenMissing() throws Exception {
        when(taskService.getTask(999L)).thenReturn(Optional.empty());

        mockMvc.perform(get("/api/tasks/999"))
                .andExpect(status().isNotFound());
    }

    @Test
    void findOverdueTasksReturnsTaskResponses() throws Exception {
        when(taskService.findOverdueTasks(any(LocalDate.class)))
                .thenReturn(List.of(sampleTask(3L, "Clean up overdue admin task", TaskStatus.TODO)));

        mockMvc.perform(get("/api/tasks/overdue"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].id").value(3L))
                .andExpect(jsonPath("$[0].title").value("Clean up overdue admin task"))
                .andExpect(jsonPath("$[0].status").value("TODO"));
    }

    @Test
    void findOverdueTasksCanFilterByPriority() throws Exception {
        when(taskService.findOverdueTasksByPriority(any(LocalDate.class), any(TaskPriority.class)))
                .thenReturn(List.of(sampleTask(3L, "Clean up overdue admin task", TaskStatus.TODO, TaskPriority.URGENT)));

        mockMvc.perform(get("/api/tasks/overdue?priority=URGENT"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].id").value(3L))
                .andExpect(jsonPath("$[0].priority").value("URGENT"));
    }

    @Test
    void createTaskReturnsCreatedTask() throws Exception {
        when(taskService.createTask(any(Task.class)))
                .thenReturn(sampleTask(1L, "Review Spring Boot API design", TaskStatus.TODO));

        mockMvc.perform(post("/api/tasks")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "title": "Review Spring Boot API design",
                                  "priority": "MEDIUM",
                                  "dueDate": "2026-06-17"
                                }
                                """))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id").value(1L))
                .andExpect(jsonPath("$.title").value("Review Spring Boot API design"))
                .andExpect(jsonPath("$.priority").value("MEDIUM"));
    }

    @Test
    void completeTaskReturnsCompletedTask() throws Exception {
        when(taskService.completeTask(1L))
                .thenReturn(Optional.of(sampleTask(1L, "Pay electricity bill", TaskStatus.DONE)));

        mockMvc.perform(patch("/api/tasks/1/complete"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("DONE"));
    }

    private Task sampleTask(Long id, String title, TaskStatus status) {
        return sampleTask(id, title, status, TaskPriority.MEDIUM);
    }

    private Task sampleTask(Long id, String title, TaskStatus status, TaskPriority priority) {
        Task task = new Task();
        task.setId(id);
        task.setTitle(title);
        task.setStatus(status);
        task.setPriority(priority);
        task.setDueDate(LocalDate.of(2026, 6, 17));
        task.setCreatedAt(OffsetDateTime.parse("2026-06-16T10:00:00+08:00"));
        task.setUpdatedAt(OffsetDateTime.parse("2026-06-16T10:00:00+08:00"));
        return task;
    }
}
