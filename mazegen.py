import random
import re

def spaces_gen(num: int) -> str:
    return "".join(' ' for _ in range(num))

class MazeGenerator:
    def __init__(self, maze_size=20):
        self.maze_size = maze_size
        self.maze = []
        self.solution_path = []
        
        # Directions for maze generation and movement
        self.directions = [
            {"dx": 0, "dy": -1, "wall": "top", "opposite": "bottom"},
            {"dx": 1, "dy": 0, "wall": "right", "opposite": "left"},
            {"dx": 0, "dy": 1, "wall": "bottom", "opposite": "top"},
            {"dx": -1, "dy": 0, "wall": "left", "opposite": "right"}
        ]
        
        # Initialize and generate the maze
        self.generate_maze()
        self.solution_path = self.find_solution()
    
    def init_maze(self):
        """Initialize maze grid with all walls intact"""
        self.maze = []
        for y in range(self.maze_size):
            row = []
            for x in range(self.maze_size):
                row.append({
                    "x": x, 
                    "y": y,
                    "walls": {"top": True, "right": True, "bottom": True, "left": True},
                    "visited": False
                })
            self.maze.append(row)
    
    def get_cell(self, x, y):
        """Retrieve cell at (x,y) or None if out of bounds"""
        if x < 0 or y < 0 or x >= self.maze_size or y >= self.maze_size:
            return None
        return self.maze[y][x]
    
    def generate_maze(self):
        """Generate maze using recursive backtracking (depth-first search)"""
        self.init_maze()
        stack = []
        current = self.maze[0][0]
        current["visited"] = True
        
        while True:
            neighbors = []
            for d in self.directions:
                next_cell = self.get_cell(current["x"] + d["dx"], current["y"] + d["dy"])
                if next_cell and not next_cell["visited"]:
                    neighbors.append({"cell": next_cell, "direction": d})
            
            if neighbors:
                rnd = random.choice(neighbors)
                current["walls"][rnd["direction"]["wall"]] = False
                rnd["cell"]["walls"][rnd["direction"]["opposite"]] = False
                stack.append(current)
                current = rnd["cell"]
                current["visited"] = True
            elif stack:
                current = stack.pop()
            else:
                break
        
        # Add extra openings to create loops (multiple valid solutions)
        extra_chance = 0.1
        for y in range(self.maze_size):
            for x in range(self.maze_size):
                for d in self.directions:
                    nx, ny = x + d["dx"], y + d["dy"]
                    neighbor = self.get_cell(nx, ny)
                    if neighbor and self.maze[y][x]["walls"][d["wall"]] and random.random() < extra_chance:
                        self.maze[y][x]["walls"][d["wall"]] = False
                        neighbor["walls"][d["opposite"]] = False
    
    def find_solution(self):
        """Find shortest solution path using breadth-first search"""
        start = self.maze[0][0]
        goal = self.maze[self.maze_size - 1][self.maze_size - 1]
        queue = []
        came_from = [[None for _ in range(self.maze_size)] for _ in range(self.maze_size)]
        visited = [[False for _ in range(self.maze_size)] for _ in range(self.maze_size)]
        
        queue.append(start)
        visited[start["y"]][start["x"]] = True
        
        while queue:
            current = queue.pop(0)
            if current == goal:
                break
            
            for d in self.directions:
                if not current["walls"][d["wall"]]:
                    nx, ny = current["x"] + d["dx"], current["y"] + d["dy"]
                    neighbor = self.get_cell(nx, ny)
                    if neighbor and not visited[ny][nx]:
                        visited[ny][nx] = True
                        came_from[ny][nx] = current
                        queue.append(neighbor)
        
        path = []
        current = goal
        while current != start:
            path.append(current)
            current = came_from[current["y"]][current["x"]]
            if not current:
                break
        
        path.append(start)
        path.reverse()
        return path
    
    def get_column_label(self, index):
        """Convert a zero-indexed column number into Excel-style label (A, B, …, AA, etc.)"""
        label = ""
        index += 1
        while index > 0:
            mod = (index - 1) % 26
            label = chr(65 + mod) + label
            index = (index - mod) // 26
        return label

    def generate_maze_text(self):
        """Generate an ASCII representation of the maze with sector indicators"""
        text = spaces_gen(5)
        # Column header
        for x in range(self.maze_size):
            text += spaces_gen(1) + self.get_column_label(x) + spaces_gen(2)
        text += "\n"
        
        # Top border (using first row's top walls)
        text += spaces_gen(4)
        for x in range(self.maze_size):
            text += "+---" if self.maze[0][x]["walls"]["top"] else "+" + spaces_gen(3)
        text += "+\n"
        
        # For each row, print the interior and bottom wall
        for y in range(self.maze_size):
            row_line = str(y+1).rjust(3) + spaces_gen(1)
            for x in range(self.maze_size):
                row_line += "|" + spaces_gen(3) if self.maze[y][x]["walls"]["left"] else spaces_gen(4)
            row_line += "|\n"
            text += row_line
            
            wall_line = spaces_gen(4)
            for x in range(self.maze_size):
                wall_line += "+---" if self.maze[y][x]["walls"]["bottom"] else "+" + spaces_gen(3)
            wall_line += "+\n"
            text += wall_line
        
        return text
    
    def parse_plan(self, input_text):
        """Parse the plan input (expects tokens like A1, B2, etc.)"""
        tokens = re.findall(r'[A-Za-z]+\d+', input_text)
        if not tokens:
            return []
        
        plan = []
        for token in tokens:
            match = re.match(r'^([A-Za-z]+)(\d+)$', token)
            if not match:
                continue
            
            col_str = match.group(1).upper()
            row_str = match.group(2)
            
            col = 0
            for char in col_str:
                col = col * 26 + (ord(char) - 64)
            col -= 1  # convert to 0-indexed
            
            row = int(row_str) - 1
            plan.append({"label": token.upper(), "x": col, "y": row})
        
        return plan
    
    def validate_plan(self, plan):
        """Validate the plan by checking adjacency and wall collisions"""
        validated = []
        errors = []
        
        if not plan:
            errors.append("No valid moves found in the plan.")
            return validated, errors
        
        # Check starting point is A1
        if plan[0]["x"] != 0 or plan[0]["y"] != 0:
            errors.append("Plan must start at A1.")
        
        # Check ending point is bottom-right
        if plan[-1]["x"] != self.maze_size - 1 or plan[-1]["y"] != self.maze_size - 1:
            errors.append(f"Plan must end at {self.get_column_label(self.maze_size - 1)}{self.maze_size}.")
        
        # Validate each move step
        for i, pos in enumerate(plan):
            cell = self.get_cell(pos["x"], pos["y"])
            error = None
            
            if not cell:
                error = f"Cell {pos['label']} is out of maze bounds."
            
            if i > 0 and not error:
                prev = plan[i - 1]
                dx = pos["x"] - prev["x"]
                dy = pos["y"] - prev["y"]
                
                if abs(dx) + abs(dy) != 1:
                    error = f"Move from {prev['label']} to {pos['label']} is not adjacent."
                else:
                    prev_cell = self.get_cell(prev["x"], prev["y"])
                    if dx == 1 and prev_cell["walls"]["right"]:
                        error = f"Wall between {prev['label']} and {pos['label']}."
                    if dx == -1 and prev_cell["walls"]["left"]:
                        error = f"Wall between {prev['label']} and {pos['label']}."
                    if dy == 1 and prev_cell["walls"]["bottom"]:
                        error = f"Wall between {prev['label']} and {pos['label']}."
                    if dy == -1 and prev_cell["walls"]["top"]:
                        error = f"Wall between {prev['label']} and {pos['label']}."
            
            cell_data = cell if cell else {"x": pos["x"], "y": pos["y"]}
            validated.append({"cell": cell_data, "label": pos["label"], "error": error})
            
            if error:
                errors.append(f"At {pos['label']}: {error}")
        
        return validated, errors

# Example usage
if __name__ == "__main__":
    # Create a maze generator with default size 20
    maze_gen = MazeGenerator(maze_size=10)
    
    # Print the maze as ASCII
    print(maze_gen.generate_maze_text())
    
    # Example plan validation
    example_plan = "A1, A2, B2, C2, C3, D3, E3, E4, E5, F5, F6, G6, G7, H7, I7, J7, J8, J9, J10"
    parsed_plan = maze_gen.parse_plan(example_plan)
    validated_plan, errors = maze_gen.validate_plan(parsed_plan)
    
    print("\nValidating example plan:")
    if errors:
        print("Errors found:")
        for error in errors:
            print(f"- {error}")
    else:
        print("Plan is valid!")
        
    # Print the solution path
    solution_coords = [(cell["x"], cell["y"]) for cell in maze_gen.solution_path]
    print("\nSolution path coordinates:", solution_coords)
    solution_labels = [f"{maze_gen.get_column_label(cell['x'])}{cell['y']+1}" for cell in maze_gen.solution_path]
    print("Solution path labels:", ", ".join(solution_labels))