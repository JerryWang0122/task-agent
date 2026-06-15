# Phase 0: Environment Setup

## Goal

Prepare the local development environment before writing application code.

## Current Tooling

- Java CLI: Java 17
- Maven: installed, but may use a newer JDK unless `JAVA_HOME` is set
- Python: available through `python3`
- Git: repository initialized

## Java Version Rule

Use Java 17 for this tutorial.

Why:

- Java 17 is a long-term support version.
- Spring Boot tutorials and enterprise projects commonly target Java 17.
- Keeping Maven and the command-line Java runtime aligned avoids confusing build issues.

To force Maven to use Java 17 in the current terminal session:

```bash
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
mvn -version
```

Expected result:

```text
Java version: 17.x
```

## Learning Point

Maven is not only a dependency manager. It also runs using a specific Java runtime.

If `java -version` and `mvn -version` show different Java versions, your application may compile or run differently depending on which command you use.
