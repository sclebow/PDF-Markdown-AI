START
|
|-- Create Tkinter root window
|-- Prompt user for OpenAI API key
|   |-- If not provided, EXIT
|
|-- Prompt user to select image directory
|   |-- If not provided, EXIT
|
|-- Prompt user to select markdown output directory
|   |-- If not provided, EXIT
|
|-- List image files in directory
|   |-- If none, EXIT
|
|-- Initialize OpenAI client
|
|-- FOR each image file:
|     |-- Check if markdown file exists
|     |   |-- If yes, SKIP
|     |
|     |-- Calculate number of patches in image
|     |-- Ask user to confirm conversion
|     |   |-- If no, SKIP
|     |
|     |-- Convert image to markdown via OpenAI API
|     |-- Save markdown to file
|     |-- Print conversion success
|
|-- Print "All images converted"
|-- Close Tkinter window
END

```mermaid
flowchart TD
    %% Nodes
    A[Start]:::start --> B[Create Tkinter root window]:::step
    B --> C[Prompt for OpenAI API key]:::step
    C -->|No key| Z1[Exit]:::exit
    C -->|Key provided| D[Prompt for image directory]:::step
    D -->|No directory| Z2[Exit]:::exit
    D -->|Directory selected| E[Prompt for markdown output directory]:::step
    E -->|No directory| Z3[Exit]:::exit
    E -->|Directory selected| F[List image files]:::step
    F -->|No images| Z4[Exit]:::exit
    F -->|Images found| G[Initialize OpenAI client]:::step
    G --> H{For each image file}:::loop
    H -->|Markdown exists| I[Skip file]:::skip
    H -->|Not exists| J[Calculate patches]:::step
    J --> K[Ask user to confirm conversion]:::step
    K -->|No| I
    K -->|Yes| L[Convert image to markdown]:::step
    L --> M[Save markdown to file]:::step
    M --> N[Print conversion success]:::step
    I --> O{More files?}:::loop
    N --> O
    O -->|Yes| H
    O -->|No| P[Print all converted]:::step
    P --> Q[Close Tkinter window]:::step
    Q --> R[End]:::en

    %% Styles
    classDef start fill:#4CAF50,stroke:#333,stroke-width:2px,color:#fff;
    classDef en fill:#2196F3,stroke:#333,stroke-width:2px,color:#fff;
    classDef exit fill:#F44336,stroke:#333,stroke-width:2px,color:#fff;
    classDef step fill:#FFF9C4,stroke:#333,stroke-width:1px;
    classDef skip fill:#BDBDBD,stroke:#333,stroke-width:1px;
    classDef loop fill:#E1BEE7,stroke:#333,stroke-width:1px;

    class A start;
    class R en;
    class Z1,Z2,Z3,Z4 exit;
    class I skip;
    class H,O loop;
```

### Partial Diagram: Get User Input and Initialize OpenAI Client

```mermaid
flowchart TD
    %% Nodes
    A[Start]:::start --> B[Create Tkinter root window]:::step
    B --> C[Prompt for OpenAI API key]:::step
    C -->|No key| Z1[Exit]:::exit
    C -->|Key provided| D[Prompt for image directory]:::step
    D -->|No directory| Z2[Exit]:::exit
    D -->|Directory selected| E[Prompt for markdown output directory]:::step
    E -->|No directory| Z3[Exit]:::exit
    E -->|Directory selected| F[List image files]:::step

    %% Styles
    classDef start fill:#4CAF50,stroke:#333,stroke-width:2px,color:#fff;
    classDef en fill:#2196F3,stroke:#333,stroke-width:2px,color:#fff;
    classDef exit fill:#F44336,stroke:#333,stroke-width:2px,color:#fff;
    classDef step fill:#FFF9C4,stroke:#333,stroke-width:1px;

    class A start;
    class R en;
    class Z1,Z2,Z3 exit;
```

### Partial Diagram: Process Each Image File

```mermaid
flowchart TD
    %% Nodes
    H{For each image file}:::loop
    H -->|Markdown exists| I[Skip file]:::skip
    H -->|Not exists| J[Calculate patches]:::step
    J --> K[Ask user to confirm conversion]:::step
    K -->|No| I
    K -->|Yes| L[Convert image to markdown]:::step
    L --> M[Save markdown to file]:::step
    M --> N[Print conversion success]:::step
    I --> O{More files?}:::loop
    N --> O
    O -->|Yes| H
    O -->|No| P[Print all converted]:::step
    P --> Q[Close Tkinter window]:::step
    Q --> R[End]:::en

    %% Styles
    classDef start fill:#4CAF50,stroke:#333,stroke-width:2px,color:#fff;
    classDef en fill:#2196F3,stroke:#333,stroke-width:2px,color:#fff;
    classDef exit fill:#F44336,stroke:#333,stroke-width:2px,color:#fff;
    classDef step fill:#FFF9C4,stroke:#333,stroke-width:1px;
    classDef skip fill:#BDBDBD,stroke:#333,stroke-width:1px;
    classDef loop fill:#E1BEE7,stroke:#333,stroke-width:1px;

    class A start;
    class R en;
    class Z1,Z2,Z3,Z4 exit;
    class I skip;
    class H,O loop;
```