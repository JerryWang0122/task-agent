package com.example.taskagent.task;

import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

import java.util.ArrayList;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class TaskDataSeederTests {

    @Test
    void runDoesNotSeedWhenTasksAlreadyExist() {
        TaskJpaRepository repository = mock(TaskJpaRepository.class);
        TaskDataSeeder seeder = new TaskDataSeeder(repository);
        when(repository.count()).thenReturn(1L);

        seeder.run();

        verify(repository, never()).saveAll(any());
    }

    @Test
    @SuppressWarnings("unchecked")
    void runSeedsSampleTasksWhenRepositoryIsEmpty() {
        TaskJpaRepository repository = mock(TaskJpaRepository.class);
        TaskDataSeeder seeder = new TaskDataSeeder(repository);
        when(repository.count()).thenReturn(0L);
        ArgumentCaptor<Iterable<Task>> tasksCaptor = ArgumentCaptor.forClass(Iterable.class);

        seeder.run();

        verify(repository).saveAll(tasksCaptor.capture());
        List<Task> seededTasks = new ArrayList<>();
        tasksCaptor.getValue().forEach(seededTasks::add);

        assertThat(seededTasks).hasSize(4);
        assertThat(seededTasks)
                .extracting(Task::getStatus)
                .contains(TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.DONE);
        assertThat(seededTasks)
                .extracting(Task::getPriority)
                .contains(TaskPriority.URGENT, TaskPriority.HIGH, TaskPriority.MEDIUM, TaskPriority.LOW);
    }
}
