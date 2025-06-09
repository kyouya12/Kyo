#Project Perancangan dan Analisa Algoritma

Team Base Project
Mata Kuliah Perancangan dan Analisis Algoritma

# Smart Courier Simulator

## Project Overview

The **Smart Courier Simulator** is a Python-based application designed to visualize and simulate the efficient movement of an autonomous courier on a digital map. This project aims to demonstrate an intelligent agent's capability in finding optimal paths within a complex environment, identifying traversable road areas, and executing a delivery task from a source point to a destination.

This simulator serves as a practical tool for understanding core concepts in pathfinding algorithms, basic image processing, and state management within a simulation system.

## Key Features

* **Custom Map Loading:** Users can load their own map images (PNG, JPG, BMP) for the simulator to process.
* **Intelligent Road Detection:** An algorithm based on color analysis identifies gray-colored road areas, even with slight color variations.
* **Map Pre-processing (Multi-layer Morphological Erosion):** Detected road areas are "cleaned" and slightly narrowed to create safer and more realistic paths for the courier, effectively preventing collisions with road edges.
* **Dynamic Position Assignment:** The courier's starting point, package pickup location (source), and delivery destination can be randomly assigned on valid road pixels.
* **A\* Pathfinding Algorithm:** Utilizes the efficient A\* algorithm with the Manhattan Distance heuristic to find the shortest path from the courier's current location to the source, and then from the source to the destination.
* **Smooth Movement Simulation:** The courier moves smoothly along the calculated path, with dynamic directional indicators.
* **Delivery Status Management:** Tracks the courier's status (has package/does not have package) and handles phase transitions (en route to pickup -> en route to delivery -> completed).
* **Intuitive User Interface:** Features clear control buttons (Load Map, Randomize, Start/Pause, Reset) and a real-time status panel.
* **Robust Error Handling:** Includes mechanisms for safe file operations and data validation, enhancing application stability.

## Why We Chose This Solution (Technical Justification)

Every technical decision in this simulator's development was carefully made based on principles of **efficiency, adaptability, visual clarity, and robustness**. We didn't just implement features; we chose the most logical and justifiable methods for this simulation scenario.

### 1. Technology Stack Selection (Python, Pygame, NumPy, Tkinter)

Our choice of **Python** as the primary programming language, supported by **Pygame** and **NumPy**, was a strategic one. Python's **readability and ease of learning** enabled rapid prototyping and efficient team collaboration. **Pygame** was the ideal library for 2D game development, providing all the necessary functionalities for graphics rendering, event handling, and frame rate control. For computationally intensive tasks like processing large map images into pixel data, **NumPy** was indispensable due to its **highly efficient array operations**, which would be significantly slower with standard Python lists. Lastly, `tkinter` was specifically chosen for the **file dialog functionality** as it offers a standard and straightforward way to interact with the user's file system graphically without the overhead of building a full GUI.

### 2. Road Detection and Pre-processing Algorithm

Accurate road detection is foundational for effective pathfinding. We opted for a **color-based detection algorithm** focusing on a **gray RGB range (90-150)** with an **RGB tolerance analysis (difference between R, G, B components $\le$ 15)**. This approach is **computationally efficient** for simple maps where roads are consistently gray. The RGB tolerance is crucial to ensure that only true gray pixels are identified, minimizing noise from slight color variations and increasing detection accuracy.

A **multi-layer morphological erosion** process was implemented as a **critical pre-processing step**. Without erosion, the courier sprite (which has a defined physical dimension) would often appear to "collide" with or get "stuck" on narrow road edges after initial color detection. This erosion process effectively **shrinks the detected road area**, creating a **safe "buffer" zone** or **wider traversable paths** for the courier. This ensures that the pathfinding algorithm will find routes that are inherently wide enough for the courier to traverse without visual glitches or actual collisions, significantly **improving simulation realism and preventing movement errors**. It's a practical way to account for the courier's physical presence on the map.

### 3. A\* Pathfinding Algorithm Implementation

The **A\*** algorithm was chosen as the core of our pathfinding system for several compelling reasons:

* **Guaranteed Optimality**: A\* guarantees finding the **shortest (optimal) path** if used with an admissible and consistent heuristic. This is paramount for a delivery simulator where route efficiency is a key performance indicator.

* **Superior Efficiency**:
    * **BFS (Breadth-First Search)**: While it guarantees the shortest path on unweighted graphs, BFS **explores the map layer by layer uniformly**. On large maps (up to 1500x1000 pixels as supported by our simulator), BFS would **explore vast, irrelevant areas**, wasting significant computational resources. It lacks "direction" towards the goal.
    * **Dijkstra's Algorithm**: Also guarantees the shortest path on non-negative weighted graphs. However, like BFS, it **does not inherently guide its search towards the target**. It expands based solely on the cost from the start, often exploring many unnecessary nodes away from the destination.
    * **Greedy Best-First Search (Greedy BFS)**: This algorithm is very fast as it **always moves towards the node that *appears* closest to the target** (based solely on its heuristic value). However, its major flaw is that it **does not guarantee the optimal (shortest) path**. It can get trapped in locally optimal paths that turn out to be much longer overall. For a courier simulator demanding the absolute shortest route, this is unacceptable.
    * **A\* (The Best of Both Worlds)**: A\* combines the best aspects of these algorithms. It leverages a **heuristic function (like Manhattan Distance)** to intelligently **guide its search towards the goal** (like Greedy BFS), while simultaneously considering the **actual cost incurred from the start** (`g_score`, like Dijkstra/BFS). This balanced approach allows A\* to **prune vast irrelevant search areas**, making it **significantly faster** than BFS or Dijkstra, while still **guaranteeing the optimal path**. This combination of speed and guaranteed optimality makes A\* the most logical and robust choice for pathfinding in this simulator.

* **Manhattan Distance Heuristic**: This heuristic was selected because it's **computationally light**, **admissible** (never overestimates the true cost), and **consistent** for the 4-way movement (horizontal/vertical) implemented. This ensures A\*'s optimal performance guarantees are met.

### 4. Sprite Design and Game Flow Control

* **Functional Sprite Design**: The courier's **triangle shape** and **4-directional sprites** were chosen for their **simplicity and clear directional indication**, avoiding the need for complex 3D assets or heavy real-time rotation algorithms. The use of **alpha channels (transparency)** ensures these sprites integrate smoothly with the map without unsightly bounding boxes.
* **Clear State Management**: Managing the game's flow through simple **global state variables** (`MAP_LOADED`, `RUNNING`, `HAS_PACKAGE`, `FINISHED`) provides a **straightforward and effective approach** for a simulation with a linear progression. This enables clear phase transitions (pickup to delivery) and responsive user controls.
* **Robustness**: Implementing **error handling (`try-except`)** for file operations and **input validation** (e.g., map size, valid path points) is crucial for the application's **stability**. These mechanisms prevent crashes from invalid user input or unexpected conditions, providing informative feedback and ensuring a more reliable user experience.

## How to Run the Simulator

To run this simulator, ensure you have Python and the necessary libraries installed.

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/kyouya12/Kyo.git](https://github.com/kyouya12/Kyo.git)
    cd Kyo
    ```
2.  **Install Dependencies:**
    ```bash
    pip install pygame numpy
    ```
    *(Tkinter is typically included with standard Python installations.)*
3.  **Run the Simulator:**
    ```bash
    python nama_file_utama_anda.py 
    # Replace 'nama_file_utama_anda.py' with the name of your main Python simulator file (e.g., main.py or simulator.py).
    ```

## Development Team

* Mhd Febri Yansah (2301020104).
* Syawal Rizal Utama (2301020008).
* Azmi Novi Athaya (2301020001).
* Ezzy Auriel Syach Lie (2301020011).

## Future Enhancements (Optional)

* **Path Visualization:** Implement an option to visually display the calculated path (e.g., a blue line) on the map.
* **8-Way Movement:** Enhance the courier's movement to include diagonal directions for potentially smoother paths.
* **More Complex Environments:** Support additional types of obstacles or different path weights.
* **Advanced Path Smoothing:** Explore more sophisticated techniques for smoothing the courier's trajectory.

## License (Optional)

[Example: This project is licensed under the MIT License. See the `LICENSE` file for details.]
