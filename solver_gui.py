import math
import time
import threading
from queue import Queue, Empty
import tkinter as tk
from tkinter import ttk, scrolledtext
from tkinter import messagebox # Import messagebox for the About dialog

# --- Solver Class (Remains Unchanged) ---
# ... (your Solver class code here, copy-paste the whole thing) ...
class Solver:
    def __init__(self, progress_queue=None):
        self.target = 0
        self.best_expression = None
        self.min_integer_count = float('inf')
        self.visited_states_count = 0 
        self.start_time = 0
        self.last_status_time = 0
        self.status_update_interval = 1 
        self.progress_queue = progress_queue 
        self._running = True 

        self.MAX_DEPTH = 9 
        self.MAX_INTERMEDIATE_VALUE = 1_000_000_000 

        self.results_by_count = [] 
        self.min_count_for_value = {} 
        self.allowed_operators = {} 

    def reset_search(self):
        self.best_expression = None
        self.min_integer_count = float('inf')
        self.visited_states_count = 0
        self.start_time = time.time()
        self.last_status_time = time.time()
        self._running = True
        self.results_by_count = [set() for _ in range(self.MAX_DEPTH + 1)]
        self.min_count_for_value = {}

    def stop_search(self):
        self._running = False

    def send_progress(self, message_type, data):
        if self.progress_queue:
            self.progress_queue.put({'type': message_type, 'data': data})

    def find_solution(self, target_value, allowed_operators):
        self.target = target_value
        self.allowed_operators = allowed_operators 
        self.reset_search()

        active_ops_display = [op for op, allowed in allowed_operators.items() if allowed]
        self.send_progress('status', f"Starting search for {target_value} with operators: {', '.join(active_ops_display) if active_ops_display else 'None Selected'}...")

        for i in range(1, 10):
            if not self._running: return None, None
            mask = 1 << (i - 1) 
            
            self.results_by_count[1].add((i, str(i), mask))
            self.min_count_for_value[i] = 1 
            self.visited_states_count += 1

            if i == self.target:
                self.best_expression = str(i)
                self.min_integer_count = 1
                self.send_progress('solution_found', {'count': 1, 'expression': str(i)})
                return self.best_expression, self.min_integer_count

        self.send_progress('status', f"Initial single digits processed. Starting iterative combinations.")

        for current_k in range(2, self.MAX_DEPTH + 1):
            if not self._running: break

            if current_k >= self.min_integer_count:
                break

            self.send_progress('status', f"Exploring expressions with {current_k} integers...")
            
            current_time = time.time()
            if current_time - self.last_status_time >= self.status_update_interval:
                self.send_progress('update_stats', {
                    'elapsed_time': current_time - self.start_time,
                    'states_per_second': self.visited_states_count / (current_time - self.start_time) if (current_time - self.start_time) > 0 else 0,
                    'visited_states': self.visited_states_count,
                    'exploring_depth': current_k,
                })
                self.last_status_time = current_time


            for i_count in range(1, current_k // 2 + 1):
                j_count = current_k - i_count

                if not self.results_by_count[i_count] or not self.results_by_count[j_count]:
                    continue

                for val_A, expr_A, mask_A in self.results_by_count[i_count]:
                    if not self._running: break
                    for val_B, expr_B, mask_B in self.results_by_count[j_count]:
                        if not self._running: break

                        new_mask = mask_A | mask_B 

                        operations_to_try = []

                        # --- Addition (Conditional) ---
                        if self.allowed_operators.get('add', False):
                            operations_to_try.append((val_A + val_B, f"({expr_A} + {expr_B})"))

                        # --- Subtraction (Conditional) ---
                        if self.allowed_operators.get('sub', False):
                            if val_A > val_B:
                                operations_to_try.append((val_A - val_B, f"({expr_A} - {expr_B})"))
                            elif val_B > val_A:
                                 operations_to_try.append((val_B - val_A, f"({expr_B} - {expr_A})"))

                        # --- Multiplication (Conditional) ---
                        if self.allowed_operators.get('mul', False):
                            operations_to_try.append((val_A * val_B, f"({expr_A} * {expr_B})"))

                        # --- Division (Conditional - MODIFIED FOR REMAINDER) ---
                        if self.allowed_operators.get('div', False):
                            # Case 1: val_A / val_B (Quotient and Remainder)
                            if val_B != 0:
                                # Quotient
                                quotient = val_A // val_B
                                operations_to_try.append((quotient, f"({expr_A} / {expr_B})")) 

                                # Remainder (only if non-zero)
                                remainder = val_A % val_B
                                if remainder != 0: 
                                    operations_to_try.append((remainder, f"({expr_A} % {expr_B})")) 

                            # Case 2: val_B / val_A (Quotient and Remainder)
                            if val_A != 0:
                                # Quotient
                                quotient = val_B // val_A
                                operations_to_try.append((quotient, f"({expr_B} / {expr_A})"))

                                # Remainder (only if non-zero)
                                remainder = val_B % val_A
                                if remainder != 0:
                                    operations_to_try.append((remainder, f"({expr_B} % {expr_A})"))

                        # --- Exponentiation (Conditional) ---
                        if self.allowed_operators.get('exp', False):
                            if val_B > 1 and val_A > 0 and val_A <= 1_000_000 and val_B < 7:
                                try:
                                    new_val_exp = val_A ** val_B
                                    if 0 <= new_val_exp <= self.MAX_INTERMEDIATE_VALUE:
                                         operations_to_try.append((new_val_exp, f"({expr_A}^{expr_B})"))
                                except OverflowError:
                                    pass 
                            if val_A > 1 and val_B > 0 and val_B <= 1_000_000 and val_A < 7:
                                try:
                                    new_val_exp = val_B ** val_A
                                    if 0 <= new_val_exp <= self.MAX_INTERMEDIATE_VALUE:
                                         operations_to_try.append((new_val_exp, f"({expr_B}^{expr_A})"))
                                except OverflowError:
                                    pass 

                        for new_val, new_expr in operations_to_try:
                            if new_val < 0 or (new_val > self.MAX_INTERMEDIATE_VALUE and new_val != self.target):
                                continue

                            if new_val in self.min_count_for_value and self.min_count_for_value[new_val] <= current_k:
                                continue 

                            if (new_val, new_expr, new_mask) not in self.results_by_count[current_k]:
                                self.results_by_count[current_k].add((new_val, new_expr, new_mask))
                                self.visited_states_count += 1

                                if new_val not in self.min_count_for_value or current_k < self.min_count_for_value[new_val]:
                                    self.min_count_for_value[new_val] = current_k

                                if new_val == self.target and current_k < self.min_integer_count:
                                    self.min_integer_count = current_k
                                    self.best_expression = new_expr
                                    self.send_progress('solution_found', {'count': current_k, 'expression': new_expr})

                    if not self._running: break
                if not self._running: break
            if not self._running: break

        elapsed_total = time.time() - self.start_time
        states_per_second_final = self.visited_states_count / elapsed_total if elapsed_total > 0 else 0

        self.send_progress('final_status', {
            'message': f"Search finished. Visited {self.visited_states_count:,} unique states in {elapsed_total:.2f} seconds ({states_per_second_final:,.0f} states/sec).",
            'total_expressions_generated': sum(len(s) for s in self.results_by_count)
        })

        if self.best_expression:
            self.send_progress('final_result', {'expression': self.best_expression, 'target': self.target, 'count': self.min_integer_count})
        else:
            self.send_progress('no_solution', {'target': self.target, 'max_depth': self.MAX_DEPTH, 'max_intermediate_value': self.MAX_INTERMEDIATE_VALUE})

        return self.best_expression, self.min_integer_count


# --- Tkinter GUI App Class (Updated with About Menu) ---
class App:
    OPERATOR_LEVELS = {
        "Addition Only": {'add': True, 'sub': False, 'mul': False, 'div': False, 'exp': False},
        "Addition & Subtraction": {'add': True, 'sub': True, 'mul': False, 'div': False, 'exp': False},
        "Add, Sub, & Multiply": {'add': True, 'sub': True, 'mul': True, 'div': False, 'exp': False},
        "All Basic Operations": {'add': True, 'sub': True, 'mul': True, 'div': True, 'exp': False},
        "All Operations (Including Exponent)": {'add': True, 'sub': True, 'mul': True, 'div': True, 'exp': True},
    }

    def __init__(self, root):
        self.root = root
        self.root.title("Number Puzzle Solver")

        self.progress_queue = Queue()
        self.solver = Solver(self.progress_queue)
        self.solver_thread = None

        self.create_menu() # NEW: Create the menu bar
        self.create_widgets()
        self.check_queue()

    # NEW method: Create the menu bar
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about_dialog)

    # NEW method: Show the About dialog
    def show_about_dialog(self):
        messagebox.showinfo(
            "About Number Puzzle Solver",
            "Application: Number Puzzle Solver\n"
            "Version: v1.0\n"
            "Description: A Python-based solver for number puzzles, designed to find arithmetic expressions using single-digit integers and selectable operations to reach a target number with minimum integers.\n\n"
            "Created by: [Your Name/Alias Here]\n"
            "Special Thanks: Developed with the assistance of Google Gemini.\n"
            "© 2024" # Current year
        )

    def create_widgets(self):
        # Input Frame
        input_frame = ttk.LabelFrame(self.root, text="Target Number")
        input_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(input_frame, text="Target:").pack(side="left", padx=5, pady=5)
        self.target_entry = ttk.Entry(input_frame, width=15)
        self.target_entry.pack(side="left", padx=5, pady=5)
        self.target_entry.insert(0, "4721") 

        self.start_button = ttk.Button(input_frame, text="Start Search", command=self.start_search)
        self.start_button.pack(side="left", padx=5, pady=5)

        self.stop_button = ttk.Button(input_frame, text="Stop Search", command=self.stop_search, state=tk.DISABLED)
        self.stop_button.pack(side="left", padx=5, pady=5)

        # Operator Selection Frame (Simplified Combobox)
        operator_select_frame = ttk.LabelFrame(self.root, text="Operator Set")
        operator_select_frame.pack(padx=10, pady=5, fill="x")

        ttk.Label(operator_select_frame, text="Select Operators:").pack(side="left", padx=5, pady=5)
        
        self.op_level_var = tk.StringVar()
        self.op_level_combobox = ttk.Combobox(
            operator_select_frame, 
            textvariable=self.op_level_var, 
            values=list(self.OPERATOR_LEVELS.keys()), 
            state="readonly"
        )
        self.op_level_combobox.pack(side="left", padx=5, pady=5)
        self.op_level_combobox.set("All Operations (Including Exponent)") 

        # Status Frame
        status_frame = ttk.LabelFrame(self.root, text="Status")
        status_frame.pack(padx=10, pady=5, fill="x")
        self.status_label = ttk.Label(status_frame, text="Ready.")
        self.status_label.pack(padx=5, pady=5, anchor="w")

        # Stats Frame
        stats_frame = ttk.LabelFrame(self.root, text="Statistics")
        stats_frame.pack(padx=10, pady=5, fill="x")
        self.elapsed_time_var = tk.StringVar(value="0.00 s")
        self.states_per_sec_var = tk.StringVar(value="0/s")
        self.visited_states_var = tk.StringVar(value="0")
        self.exploring_depth_var = tk.StringVar(value="0")

        ttk.Label(stats_frame, text="Elapsed Time:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(stats_frame, textvariable=self.elapsed_time_var).grid(row=0, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(stats_frame, text="States/Sec:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(stats_frame, textvariable=self.states_per_sec_var).grid(row=1, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(stats_frame, text="Visited States:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(stats_frame, textvariable=self.visited_states_var).grid(row=2, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(stats_frame, text="Exploring Depth:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(stats_frame, textvariable=self.exploring_depth_var).grid(row=3, column=1, sticky="w", padx=5, pady=2)
        
        # Solution Frame
        solution_frame = ttk.LabelFrame(self.root, text="Solution")
        solution_frame.pack(padx=10, pady=5, fill="x")
        ttk.Label(solution_frame, text="Expression:").pack(side="left", padx=5, pady=5)
        self.solution_var = tk.StringVar()
        self.solution_entry = ttk.Entry(solution_frame, textvariable=self.solution_var, state='readonly', width=50)
        self.solution_entry.pack(side="left", padx=5, pady=5)

        # Log Frame
        log_frame = ttk.LabelFrame(self.root, text="Log")
        log_frame.pack(padx=10, pady=10, fill="both", expand=True)
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=10)
        self.log_text.pack(padx=5, pady=5, fill="both", expand=True)
        self.log_text.config(state='disabled')

    def log_message(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def start_search(self):
        if self.solver_thread and self.solver_thread.is_alive():
            self.log_message("Search already running.")
            return

        try:
            target_value = int(self.target_entry.get())
            if target_value <= 0:
                self.log_message("Please enter a positive integer target.")
                return
        except ValueError:
            self.log_message("Invalid target. Please enter an integer.")
            return

        selected_level_name = self.op_level_combobox.get()
        if not selected_level_name:
            self.log_message("Please select an operator set.")
            return
            
        allowed_operators = self.OPERATOR_LEVELS.get(selected_level_name)
        if allowed_operators is None:
            self.log_message("Error: Invalid operator set selected. Please choose from the list.")
            return

        self.reset_gui_for_new_search()
        
        self.solver_thread = threading.Thread(target=self.solver.find_solution, args=(target_value, allowed_operators,))
        self.solver_thread.daemon = True
        self.solver.reset_search() 
        self.solver_thread.start()

        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.log_message(f"Search started for target: {target_value}")

    def stop_search(self):
        if self.solver_thread and self.solver_thread.is_alive():
            self.solver.stop_search()
            self.log_message("Stopping search...")
            self.root.after(500, self._check_thread_stopped)
        else:
            self.log_message("No search running to stop.")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)

    def _check_thread_stopped(self):
        if self.solver_thread and self.solver_thread.is_alive():
            self.root.after(500, self._check_thread_stopped)
        else:
            self.log_message("Search thread stopped.")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)

    def reset_gui_for_new_search(self):
        self.solution_var.set("")
        self.elapsed_time_var.set("0.00 s")
        self.states_per_sec_var.set("0/s")
        self.visited_states_var.set("0")
        self.exploring_depth_var.set("0")
        self.status_label.config(text="Ready.")
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state='disabled')


    def check_queue(self):
        while True:
            try:
                msg = self.progress_queue.get_nowait()
                msg_type = msg['type']
                msg_data = msg['data']

                if msg_type == 'status':
                    self.status_label.config(text=msg_data)
                    self.log_message(msg_data)
                elif msg_type == 'update_stats':
                    self.elapsed_time_var.set(f"{msg_data['elapsed_time']:.2f} s")
                    self.states_per_sec_var.set(f"{msg_data['states_per_second']:.0f}/s")
                    self.visited_states_var.set(f"{msg_data['visited_states']:,}")
                    self.exploring_depth_var.set(f"{msg_data['exploring_depth']}")
                elif msg_type == 'solution_found':
                    self.log_message(f"SOLUTION FOUND! {msg_data['expression']} = {self.solver.target} (using {msg_data['count']} integers)")
                    self.solution_var.set(msg_data['expression'])
                elif msg_type == 'final_status':
                    self.log_message(msg_data['message'])
                    if 'total_expressions_generated' in msg_data:
                        self.log_message(f"Total unique expressions generated: {msg_data['total_expressions_generated']:,}")
                    self.start_button.config(state=tk.NORMAL)
                    self.stop_button.config(state=tk.DISABLED)
                elif msg_type == 'final_result':
                    self.log_message(f"FINAL RESULT: {msg_data['expression']} = {msg_data['target']} (using {msg_data['count']} integers)")
                elif msg_type == 'no_solution':
                    self.log_message(f"No solution found for {msg_data['target']} within MAX_DEPTH={msg_data['max_depth']} or MAX_INTERMEDIATE_VALUE={msg_data['max_intermediate_value']:,}.")
                    self.start_button.config(state=tk.NORMAL)
                    self.stop_button.config(state=tk.DISABLED)

            except Empty:
                break
            except Exception as e:
                self.log_message(f"Error processing queue message: {e}")
                self.start_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.DISABLED)
                break
        self.root.after(100, self.check_queue)

# --- Main execution block ---
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()