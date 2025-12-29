# Level Maze - Game Design Document

**Version:** 1.7  
**Status:** Draft  

## 1. Game Overview
**Level Maze** is a top-down action game where players navigate a series of maze-like arenas, evading enemies and finding the exit. The game emphasizes spatial awareness, precise movement, and stealth/evasion tactics against line-of-sight based enemies.

## 2. Core Gameplay Mechanics

### 2.1 Perspective
*   **View:** Top-down (Bird's-eye view).
*   **Camera:** Fixed or following the player (to be determined during implementation of arena size).

### 2.2 Controls
The game utilizes a dual-stick controller scheme with a unique mapping configuration:
*   **Sticks:**
    *   **Left Stick:** Controls **Motion Direction** (Movement). The player moves in the direction the stick is pushed, independent of facing.
    *   **Right Stick:** Controls **Look Direction** (Rotation). The player character rotates to face the direction the stick is pushed.
    *   *Note:* This separates movement vector from look vector, allowing for strafing and backing away while watching enemies.
*   **Buttons:**
    *   **Select Button:** Toggles the **Help Overlay**.

### 2.3 Combat & Physics Interactions
*   **Health Points (HP):** The **Player**, **Enemies**, and **Obstacles** all possess a Health Point (HP) value.
*   **Collision & Damage Rules:**
    *   **Player vs. Enemy (Dynamic Interaction):**
        *   **Damage:** **Both** entities take damage immediately upon contact.
        *   **Response:** Both entities are repelled (bounced) away from each other.
        *   **Bounce Magnitude:** The distance of the bounce is directly proportional to the damage taken (`Distance = k * Damage`).
    *   **Entity vs. Environment (Static Interaction):**
        *   **Scope:** Includes Player/Enemy collisions with **Arena Boundaries** or **Obstacles**.
        *   **Damage:** **NO Damage** is applied to any party. The Arena and Obstacles are immune to collision damage from entities, and entities do not take damage from hitting walls.
        *   **Response:** Purely physical blocking; players/enemies slide along or stop at the wall.
*   *Note:* While Obstacles have HP (as defined in 2.3.1), this is reserved for specific destruction mechanics (e.g., explosions), not simple collisions.

## 3. Game Elements

### 3.1 The Player
*   **Visual Representation:** simple circle.
*   **Properties:**
    *   **Health (HP):** Finite health value.
    *   **Experience (XP):** XP points are earned and used to level up Abilities.
        *   **Gain Mechanics:** XP is awarded for:
            1.  **Killing Enemies.**
            2.  **Exiting the Arena** (Completing the level).
*   **Direction Indicator:** A small arrow on the periphery of the circle indicates the current "Look" direction.
*   **Collision:** stiff body physics. The player cannot pass through:
    *   Arena Edges (Boundaries)
    *   Obstacles
*   **Abilities:**
    *   **1. Dash:**
        *   **Effect:** Grants a burst of speed, moving the player **2 times its diameter** in the current *facing* direction (Left Stick direction).
        *   **Cooldown:** **10 Seconds**.
    *   **2. Roar:**
        *   **Effect:** Emits a shockwave that pushes all nearby enemies away from the player.
        *   **Push Distance:** **5 times the player's diameter**.
        *   **Damage:** **0**. (Crowd control only).
        *   **Cooldown:** **30 Seconds**.

### 3.2 The Arena
*   **Shape:** Rectangular.
*   **Boundaries:** Solid walls enclosing the play area.
*   **Access Points:**
    *   **Entry:** A gap in the boundary wall (start point).
    *   **Exit:** A gap in the boundary wall (end point/goal).
*   **Visual Style:**
    *   **Texture:** Brick texture is the default for boundaries.
    *   **Customization:** The texture system must be modular to support different themes/materials for future levels.

### 3.3 Obstacles
*   **Properties:**
    *   **Health (HP):** Finite health value.
*   **Composition:** Rectangular shapes.
*   **Material:** Same visual texture as the Arena Boundaries (e.g., Brick).
*   **Placement:** Randomly positioned within the arena.
*   **Layout Constraints:**
    *   **Spacing:** A guaranteed minimum distance must be maintained between any two obstacle edges.
    *   **Minimum Gap:** `1.5 * Player Diameter`. This ensures the player can always navigate between any two valid obstacles without getting stuck.

### 3.4 Enemies
*   **Visual Representation:**
    *   Shape: Circle (same size as the Player).
    *   Color: Distinct from Player (e.g., Red vs. Blue).
    *   Direction Indicator: Arrow indicating current facing/movement direction.
*   **Properties:**
    *   **Health (HP):** Finite health value.
*   **Movement Constraints:**
    *   "Tank" style movement or forward-only drive: Enemies can only move in the direction they are currently looking.
*   **Vision & AI:**
    *   **Line of Sight (LOS):** Enemies see in straight lines. Vision is blocked by:
        *   Arena Boundaries
        *   Obstacles
    *   **Behavior States:**
        1.  **Patrol/Wander:** If the player is not seen, the enemy moves in a random direction.
        2.  **Chase:** If the player enters LOS, the enemy rotates and moves directly towards the player.
        3.  **Investigate:** If the player breaks LOS (hides), the enemy continues to the *last known position* of the player. Once arrived, if player is still unseen, revert to Patrol/Wander.

### 3.5 Xtras (Power-ups)
A modular system for spawnable items that provide temporary benefits.
*   **General Spawning Rules:**
    *   **Location:** Randomly positioned within the arena.
    *   **Constraint:** Must spawn in **empty space**. Never spawns inside Obstacles or Walls.
    *   **Lifetime:** Xtras remain in the arena for **10 Seconds** before disappearing if not collected.
*   **Items:**
    *   **1. Health Pack:**
        *   **Visual:** Square shape with a "Health" symbol.
        *   **Effect:** Restores Health Points (HP) upon contact.
        *   **Collection Logic:**
            *   **Player:** Restores **100%** of the pack's health value.
            *   **Enemy:** Restores **50%** of the pack's health value.

### 3.6 User Interface (UI)
*   **Help Overlay:**
    *   **Trigger:** Pressing the **Select** button on the controller.
    *   **Function:** Displays a screen overlay explaining the game controls (Sticks/Abilities) and basic rules.
    *   **Behavior:** Pauses/interrupts gameplay while active (TBC based on engine pausing capabilities, but functionally blocks view).

## 4. System Architecture & Modularity
The game system is designed with strict modularity to ensure that the Arena, Obstacles, Enemies, and Player are decoupled components. This allows for independent modification, testing, and expansion of each element without causing regressions in others.

### 4.1 Core Philosophy
*   **Decoupling:** No hard dependencies between concrete classes. Interaction is managed through interfaces and a central Game Manager or Event System.
*   **Data-Driven:** Properties (speed, size, texture, health) are defined in external configuration files or scriptable objects, not hard-coded.

### 4.2 Component Specifications

#### 4.2.1 Arena System (The Container)
*   **Responsibility:** Defines the playable space, boundaries, and level exit/entry.
*   **Modularity Spec:**
    *   **Shape Agnostic:** The underlying logic supports any closed polygon, not just rectangles.
    *   **Texture Independence:** The visual material (e.g., Brick) is a separate material layer applied to the geometry. Changing the texture does not affect the physical collider boundaries.
    *   **Hot-Swappable:** The Arena can be swapped at runtime (e.g., loading a next level) without resetting the Player or Enemy systems.

#### 4.2.2 Obstacle System (The Static Elements)
*   **Responsibility:** Provides impedance and cover within the Arena.
*   **Modularity Spec:**
    *   **Placement Logic:** Obstacles utilize a "Safe Spawn" algorithm that queries the Arena for valid bounds and checks against a "Minimum Separation" setting. This logic is independent of the *type* of obstacle.
    *   **Shape Polymorphism:** While currently rectangular, the system treats obstacles as generic `IObstacle` entities. Replacing a box with a barrel or column requires no code changes in the pathfinding or arena systems.

#### 4.2.3 Enemy System ( The Dynamic Agents)
*   **Responsibility:** Hostile entities that track and pursue the player.
*   **Modularity Spec:**
    *   **Sensor Independence:** The "Vision" module (LOS check) is a separate component. It queries the physics world for *any* blocking layer (Arena or Obstacle) without knowing what specifically blocked it.
    *   **Movement Abstraction:** Locomotion is handled by a `IMovementController`. The AI sends a desire (e.g., "Target Position: (x,y)"), and the controller handles the physics. This allows swapping "Tank treads" for "Hover movement" without rewriting the AI logic.
    *   **Type Swapping:** A unified `EnemyManager` can spawn different enemy prefabs/types into the same arena configuration seamlessly.

#### 4.2.4 Player System (The Controller)
*   **Responsibility:** Interprets user input and renders the avatar.
*   **Modularity Spec:**
    *   **Input Abstraction:** The `InputHandler` reads hardware states (sticks) and converts them to generic `GameEvents` (MoveVector, LookVector). The Player entity consumes these events, meaning the controller hardware can be changed (e.g., Keyboard vs. Gamepad) without touching the Player code.
    *   **Visual Separation:** The "Circle with Arrow" is a child view component. The collision logic is on the parent root. You can replace the circle sprite with a character model without altering the collision size or movement physics.

#### 4.2.5 Xtras System (Power-ups)
*   **Responsibility:** Manages the spawning, lifetime, and effects of pick-up items.
*   **Modularity Spec:**
    *   **Spawn Strategy:** The `XtraManager` handles *where* and *when* to spawn items, ensuring no overlaps with obstacles. It is agnostic of *what* item is spawned.
    *   **Effect Interface:** Items implement an `ICollectible` interface (e.g., `OnCollect(GameObject target)`). This allows adding new items (Speed Boost, Shield) without changing the spawning logic.

## 5. Project Structure
To support modularity and distribution, the project utilizes a standard package layout:
*   **Package Folder:** The core game logic must be contained within a dedicated package folder (e.g., `level_maze/`).
*   **Source Organization:** All game modules (Player, Arena, Obstacles, Enemies) reside within this package.
*   **Configuration (`config.yaml`):**
    *   A central configuration file must be present within the package to allow for non-code adjustments to game balance.
    *   **Required Configurable Fields:**
        *   `abilities.dash.cooldown` (Default: 10.0)
        *   `abilities.dash.distance_multiplier` (Default: 2.0)
        *   `abilities.roar.cooldown` (Default: 30.0)
        *   `abilities.roar.push_distance_multiplier` (Default: 5.0)
        *   `abilities.current_levels` (For save/load state)
