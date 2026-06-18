package com.example.taskagent.task;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class TaskApiIntegrationTests {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private TaskJpaRepository taskJpaRepository;

    @BeforeEach
    void cleanDatabase() {
        taskJpaRepository.deleteAll();
    }

    @Test
    void createTaskPersistsThroughRestApi() throws Exception {
        mockMvc.perform(post("/api/tasks")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "title": "Prepare weekly report",
                                  "priority": "HIGH",
                                  "dueDate": "2026-06-17"
                                }
                                """))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id").isNumber())
                .andExpect(jsonPath("$.title").value("Prepare weekly report"))
                .andExpect(jsonPath("$.status").value("TODO"));

        mockMvc.perform(get("/api/tasks"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].title").value("Prepare weekly report"))
                .andExpect(jsonPath("$[0].priority").value("HIGH"));
    }
}
