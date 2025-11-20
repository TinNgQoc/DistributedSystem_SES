"""
SES Algorithm Implementation - Schiper-Eggli-Sandoz
Vector structure V_P with (destination, timestamp) pairs
"""

class SESVector:
    """
    V_P structure for SES Algorithm
    Each process maintains V_P containing (P', t) pairs where:
    - P' is destination process id
    - t is vector timestamp (array of N integers)
    """
    
    def __init__(self, num_processes, process_id):
        """
        Initialize SES Vector structure
        
        Args:
            num_processes: Number of processes in the system
            process_id: ID of current process
        """
        self.num_processes = num_processes
        self.process_id = process_id
        # Vector timestamp (like traditional vector clock)
        self.vector_time = [0] * num_processes
        # V_P structure: dictionary {dest_pid: vector_timestamp}
        # Initially empty
        self.v_p = {}
    
    def increment_local_time(self):
        """
        Increment own position in vector timestamp on internal event or send
        """
        self.vector_time[self.process_id] += 1
    
    def get_local_time(self):
        """
        Get current vector timestamp
        """
        return self.vector_time.copy()
    
    def update_local_time(self, received_vector):
        """
        Update vector time with received vector (component-wise max) + increment
        Standard vector clock update rules
        """
        for i in range(self.num_processes):
            self.vector_time[i] = max(self.vector_time[i], received_vector[i])
        # Increment own position
        self.increment_local_time()
    
    def add_destination(self, dest_pid, timestamp_vector):
        """
        Add or update (dest_pid, timestamp) in V_P
        Overwrites if dest_pid already exists
        
        Args:
            dest_pid: Destination process ID
            timestamp_vector: Vector timestamp to associate (list of N integers)
        """
        self.v_p[dest_pid] = timestamp_vector.copy()
    
    def get_v_p_copy(self):
        """
        Get a copy of V_P
        
        Returns:
            Dictionary copy of V_P
        """
        return {k: v.copy() for k, v in self.v_p.items()}
    
    def merge_v_m(self, v_m):
        """
        Merge V_M from received message with local V_P
        Rules:
        - If (P,t) not in V_P, add it
        - If (P,t) exists in V_P, update with component-wise maximum
        
        Args:
            v_m: V_M from received message (dictionary {pid: vector})
        """
        for pid, t_vector in v_m.items():
            if pid not in self.v_p:
                # Not present, add it
                self.v_p[pid] = t_vector.copy()
            else:
                # Present, take component-wise maximum
                self.v_p[pid] = [max(t_vector[i], self.v_p[pid][i]) for i in range(len(t_vector))]
    
    def check_in_v_p(self, dest_pid):
        """
        Check if dest_pid exists in V_P
        """
        return dest_pid in self.v_p
    
    def get_t_for_dest(self, dest_pid):
        """
        Get timestamp vector associated with dest_pid in V_P
        """
        return self.v_p.get(dest_pid, None)
    
    def compare_vectors(self, v1, v2):
        """
        Compare two vectors: returns True if v1 > v2 (all components)
        v1 > v2 means: for all i, v1[i] > v2[i]
        """
        return all(v1[i] > v2[i] for i in range(len(v1)))
    
    def compare_vectors_leq(self, v1, v2):
        """
        Compare two vectors: returns True if v1 <= v2 (all components)
        v1 <= v2 means: for all i, v1[i] <= v2[i]
        """
        return all(v1[i] <= v2[i] for i in range(len(v1)))
    
    def __str__(self):
        """
        String representation
        """
        return f"t_P{self.process_id}={self.vector_time}, V_P={self.v_p}"
    
    def __repr__(self):
        return f"SESVector(pid={self.process_id}, t={self.vector_time}, V_P={self.v_p})"
