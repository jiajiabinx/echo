document.getElementById('userForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    // Get form data
    const formData = {
        birth_date: document.getElementById('birth_date').value,
        birth_location: document.getElementById('birth_location').value,
        primary_residence: document.getElementById('primary_residence').value,
        current_location: document.getElementById('current_location').value,
        college: document.getElementById('college').value,
        educational_level: document.getElementById('educational_level').value,
        parental_income: parseInt(document.getElementById('parental_income').value),
        primary_interest: document.getElementById('primary_interest').value,
        profession: document.getElementById('profession').value,
        religion: document.getElementById('religion').value,
        race: document.getElementById('race').value
    };

    try {
        const response = await fetch('/api/users', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            alert('Registration successful!');
            this.reset(); // Reset form after successful submission
        } else {
            const error = await response.json();
            alert(`Registration failed: ${error.message}`);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred during registration.');
    }
});

// Set max date for birth_date to today
document.getElementById('birth_date').max = new Date().toISOString().split('T')[0]; 