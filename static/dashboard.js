document.addEventListener('DOMContentLoaded', function () {
    // Get the input fields for filtering
    const studentNameInput = document.getElementById('student_name');
    const courseInput = document.getElementById('course');

    // Get all rows of the attendance table
    const tableRows = document.querySelectorAll('.attendance-table-section tbody tr');

    // Function to apply filtering based on input fields
    function applyFilters() {
        const studentNameFilter = studentNameInput.value.toLowerCase();
        const courseFilter = courseInput.value.toLowerCase();

        // Loop through each row of the attendance table
        tableRows.forEach(row => {
            const studentName = row.cells[0].textContent.toLowerCase();
            const course = row.cells[1].textContent.toLowerCase();

            // Hide the row if it doesn't match the filter criteria
            if (
                (studentNameFilter && studentName.indexOf(studentNameFilter) === -1) ||
                (courseFilter && course.indexOf(courseFilter) === -1)
            ) {
                row.style.display = 'none';
            } else {
                row.style.display = '';
            }
        });
    }

    // Add event listeners to input fields to trigger filtering on input change
    studentNameInput.addEventListener('input', applyFilters);
    courseInput.addEventListener('input', applyFilters);
});
