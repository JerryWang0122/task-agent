package com.example.taskagent.task;

import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Optional;

@Service
public class TaskService {

    private final TaskJpaRepository taskRepository;

    public TaskService(TaskJpaRepository taskRepository) {
        this.taskRepository = taskRepository;
    }

    public List<Task> listTasks() {
        return taskRepository.findAll(Sort.by(Sort.Direction.ASC, "id"));
    }

    public Optional<Task> getTask(Long id) {
        return taskRepository.findById(id);
    }

    public List<Task> findOverdueTasks(LocalDate today) {
        return taskRepository.findByDueDateBeforeAndStatusNot(
                today,
                TaskStatus.DONE,
                Sort.by(Sort.Direction.ASC, "dueDate", "id")
        );
    }

    public Task createTask(Task task) {
        OffsetDateTime now = OffsetDateTime.now();

        if (task.getStatus() == null) {
            task.setStatus(TaskStatus.TODO);
        }
        if (task.getPriority() == null) {
            task.setPriority(TaskPriority.MEDIUM);
        }
        if (task.getCreatedAt() == null) {
            task.setCreatedAt(now);
        }
        task.setUpdatedAt(now);

        return taskRepository.save(task);
    }

    public Optional<Task> completeTask(Long id) {
        return taskRepository.findById(id)
                .map(task -> {
                    task.setStatus(TaskStatus.DONE);
                    task.setUpdatedAt(OffsetDateTime.now());
                    return taskRepository.save(task);
                });
    }

    public boolean deleteTask(Long id) {
        if (!taskRepository.existsById(id)) {
            return false;
        }

        taskRepository.deleteById(id);
        return true;
    }
}
