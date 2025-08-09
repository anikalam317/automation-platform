# Recipe Creation

TODO: Need to determine how the users will create new recipes.
### 3.1 External Task Definitions

In some cases a task may include a complex operation that is better defined
in another vendor software. For example, a task running an HPLC method might
use the instruments vendor software to define the method and execute it. In this case,
the task definition in LAF would include a reference to the external method
(how to execute it, such as the file path or API endpoint, and any additional
parameters, such as user who is executing the task, sample ID, etc.). This
information should be stored in the database as part of the task definition.
This is kind of like the concept of data fabric, where data and metadata
are managed in a unified way across different systems. For this workflow
platform, we can think of the task definition as a piece of metadata that
describes how to execute a specific operation, regardless of where or how
it is actually executed (i.e. a "workflow fabric").

### 3.2 Task Definition and Compliance

- Tasks are defined using a flexible JSON schema ("recipe") stored in the database, allowing support for a wide variety of operations (instrument control, calculations, notifications, external system integration, etc.).
- Each task's recipe is validated using user-extensible Pydantic schemas, enabling companies to define custom task types without modifying the core LAF database model.
- For tasks defined in external systems (e.g., ELNs like Biovia Onelab), the recipe can include references (URLs, IDs) and a snapshot of the external data for compliance and reproducibility.
- Hashes and sync status can be used to detect changes in external definitions and mark workflows as invalid if compliance is affected.
- This approach balances flexibility (easy addition of new task types) and compliance (audit trails, reproducibility, traceability), while keeping the core platform vendor-agnostic and maintainable.
---

