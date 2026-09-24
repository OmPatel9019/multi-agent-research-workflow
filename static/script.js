document.addEventListener('DOMContentLoaded', () => {
    const travelForm = document.getElementById('travelForm');
    const userQueryInput = document.getElementById('userQuery');
    const submitBtn = document.getElementById('submitBtn');
    const chips = document.querySelectorAll('.chip');

    const pipelineSection = document.getElementById('pipelineSection');
    const pipelineTimer = document.getElementById('pipelineTimer');
    const statusNotification = document.getElementById('statusNotification');

    const stepFlight = document.getElementById('step-flight');
    const stepHotel = document.getElementById('step-hotel');
    const stepPlanner = document.getElementById('step-planner');

    const resultsSection = document.getElementById('resultsSection');
    const emptyState = document.getElementById('emptyState');
    const streamingOutput = document.getElementById('streamingOutput');
    const typingCursor = document.getElementById('typingCursor');
    const flightsOutput = document.getElementById('flightsOutput');
    const hotelsOutput = document.getElementById('hotelsOutput');

    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const copyBtn = document.getElementById('copyBtn');
    const printBtn = document.getElementById('printBtn');

    let timerInterval = null;
    let startTime = null;
    let accumulatedMarkdown = "";

    // Quick Prompt Chips
    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            userQueryInput.value = chip.getAttribute('data-prompt');
            userQueryInput.focus();
        });
    });

    // Tab Switching
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
        });
    });

    // Copy Itinerary
    copyBtn.addEventListener('click', async () => {
        if (!accumulatedMarkdown) return;
        try {
            await navigator.clipboard.writeText(accumulatedMarkdown);
            const originalHtml = copyBtn.innerHTML;
            copyBtn.textContent = 'Copied';
            setTimeout(() => { copyBtn.innerHTML = originalHtml; }, 2000);
        } catch (err) {
            console.error('Failed to copy text: ', err);
        }
    });

    // Print Plan
    printBtn.addEventListener('click', () => {
        window.print();
    });

    // Pipeline Step UI Helpers
    function setStepState(stepElement, state, customStatus) {
        stepElement.classList.remove('running', 'done');
        const badge = stepElement.querySelector('.step-badge');
        const statusText = stepElement.querySelector('.step-status');

        if (state === 'running') {
            stepElement.classList.add('running');
            badge.className = 'step-badge running';
            badge.textContent = '...';
            statusText.textContent = customStatus || 'Executing...';
        } else if (state === 'done') {
            stepElement.classList.add('done');
            badge.className = 'step-badge done';
            badge.textContent = 'OK';
            statusText.textContent = customStatus || 'Completed';
        } else {
            badge.className = 'step-badge pending';
            badge.textContent = '-';
            statusText.textContent = 'Waiting...';
        }
    }

    function resetPipeline() {
        setStepState(stepFlight, 'pending');
        setStepState(stepHotel, 'pending');
        setStepState(stepPlanner, 'pending');
        statusNotification.textContent = 'Preparing your research...';
        pipelineTimer.textContent = '0.0s elapsed';
        accumulatedMarkdown = "";
        streamingOutput.innerHTML = "";
        typingCursor.classList.remove('hidden');
    }

    function startTimer() {
        startTime = Date.now();
        timerInterval = setInterval(() => {
            const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
            pipelineTimer.textContent = `${elapsed}s elapsed`;
        }, 100);
    }

    function stopTimer() {
        if (timerInterval) {
            clearInterval(timerInterval);
            timerInterval = null;
        }
    }

    // Form Submission & Live SSE Streaming
    travelForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const query = userQueryInput.value.trim();
        if (!query) return;

        // UI Reset
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="btn-text">Researching...</span><span class="btn-icon" aria-hidden="true">...</span>';
        pipelineSection.classList.remove('hidden');
        resultsSection.classList.remove('hidden');
        emptyState.classList.add('hidden');
        resetPipeline();
        startTimer();

        // Switch to master plan tab
        document.querySelector('[data-tab="itineraryTab"]').click();

        try {
            const response = await fetch('/api/travel/stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: query })
            });

            if (!response.ok) {
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let buffer = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n\n');
                buffer = lines.pop(); // Keep incomplete chunk in buffer

                for (const block of lines) {
                    if (!block.trim()) continue;

                    let eventType = 'message';
                    let eventData = '';

                    const sublines = block.split('\n');
                    for (const line of sublines) {
                        if (line.startsWith('event:')) {
                            eventType = line.replace('event:', '').trim();
                        } else if (line.startsWith('data:')) {
                            eventData = line.replace('data:', '').trim();
                        }
                    }

                    if (!eventData) continue;

                    try {
                        const payload = JSON.parse(eventData);

                        if (eventType === 'status') {
                            const { stage, message } = payload;
                            statusNotification.textContent = message;

                            if (stage === 'flight') {
                                setStepState(stepFlight, 'running', 'Searching flights...');
                            } else if (stage === 'hotel') {
                                setStepState(stepHotel, 'running', 'Finding stays...');
                            } else if (stage === 'planner') {
                                setStepState(stepFlight, 'done');
                                setStepState(stepHotel, 'done');
                                setStepState(stepPlanner, 'running', 'Synthesizing plan...');
                            }
                        } 
                        else if (eventType === 'research') {
                            const { type, content } = payload;
                            if (type === 'flights') {
                                setStepState(stepFlight, 'done');
                                flightsOutput.innerHTML = marked.parse(content || 'No flights found.');
                            } else if (type === 'hotels') {
                                setStepState(stepHotel, 'done');
                                hotelsOutput.innerHTML = marked.parse(content || 'No hotels found.');
                            }
                        } 
                        else if (eventType === 'token') {
                            accumulatedMarkdown += payload.token;
                            streamingOutput.innerHTML = marked.parse(accumulatedMarkdown);
                        } 
                        else if (eventType === 'done') {
                            setStepState(stepFlight, 'done');
                            setStepState(stepHotel, 'done');
                            setStepState(stepPlanner, 'done');
                            statusNotification.textContent = 'Travel plan synthesized successfully.';
                            typingCursor.classList.add('hidden');
                            stopTimer();
                        }
                    } catch (parseErr) {
                        console.warn('Error parsing SSE event:', parseErr, eventData);
                    }
                }
            }

        } catch (err) {
            console.error('Streaming request error:', err);
            statusNotification.textContent = `Error: ${err.message}`;
            streamingOutput.innerHTML += `<div style="color: var(--danger); margin-top: 16px;"><strong>Request failed:</strong> ${err.message}</div>`;
            typingCursor.classList.add('hidden');
            stopTimer();
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span class="btn-text">Build my itinerary</span><span class="btn-icon" aria-hidden="true">-&gt;</span>';
        }
    });
});
