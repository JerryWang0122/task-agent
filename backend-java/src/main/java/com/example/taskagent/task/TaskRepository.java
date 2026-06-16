package com.example.taskagent.task;

import org.springframework.stereotype.Repository;

import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicLong;

@Repository
public class TaskRepository {

    private final Map<Long, Task> tasks = new LinkedHashMap<>();
    private final AtomicLong nextId = new AtomicLong(1);

    public synchronized List<Task> findAll() {
        return new ArrayList<>(tasks.values());
    }

    public synchronized Optional<Task> findById(Long id) {
        return Optional.ofNullable(tasks.get(id));
    }

    public synchronized Task save(Task task) {
        OffsetDateTime now = OffsetDateTime.now();

        if (task.getId() == null) {
            task.setId(nextId.getAndIncrement());
            task.setCreatedAt(now);
        }

        task.setUpdatedAt(now);
        tasks.put(task.getId(), task);

        return task;
    }

    public synchronized boolean deleteById(Long id) {
        return tasks.remove(id) != null;
    }
}
