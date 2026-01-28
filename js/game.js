const canvas = document.getElementById('game-canvas');
const ctx = canvas.getContext('2d');
const startBtn = document.getElementById('start-btn');
const pauseBtn = document.getElementById('pause-btn');
const restartBtn = document.getElementById('restart-btn');
const speedSelect = document.getElementById('speed-select');
const scoreDisplay = document.getElementById('score');
const finalScoreDisplay = document.getElementById('final-score');
const gameOverModal = document.getElementById('game-over-modal');

// Game Constants
const GRID_SIZE = 20;
const TILE_COUNT = canvas.width / GRID_SIZE;

// Game State
let snake = [];
let food = { x: 0, y: 0 };
let dx = 0;
let dy = 0;
let score = 0;
let gameInterval;
let isGameRunning = false;
let isPaused = false;
let gameSpeed = 150;
let changingDirection = false;

// Initialize Game State
function initGame() {
    snake = [
        { x: 10, y: 10 },
        { x: 9, y: 10 },
        { x: 8, y: 10 }
    ];
    score = 0;
    dx = 1; // Start moving right
    dy = 0;
    scoreDisplay.textContent = score;
    spawnFood();
    changingDirection = false;
    draw();
}

// Spawn Food
function spawnFood() {
    food.x = Math.floor(Math.random() * TILE_COUNT);
    food.y = Math.floor(Math.random() * TILE_COUNT);

    // Check if food spawns on snake body
    for (let part of snake) {
        if (part.x === food.x && part.y === food.y) {
            spawnFood();
            break;
        }
    }
}

// Main Game Loop
function gameLoop() {
    if (isPaused) return;

    changingDirection = false;
    update();
    draw();
}

// Update Logic
function update() {
    const head = { x: snake[0].x + dx, y: snake[0].y + dy };

    // Wall Collision Check
    if (head.x < 0 || head.x >= TILE_COUNT || head.y < 0 || head.y >= TILE_COUNT) {
        gameOver();
        return;
    }

    // Self Collision Check
    for (let i = 0; i < snake.length; i++) {
        if (head.x === snake[i].x && head.y === snake[i].y) {
            gameOver();
            return;
        }
    }

    snake.unshift(head);

    // Eat Food
    if (head.x === food.x && head.y === food.y) {
        score += 10;
        scoreDisplay.textContent = score;
        spawnFood();
    } else {
        snake.pop();
    }
}

// Draw Logic
function draw() {
    // Clear Canvas
    ctx.fillStyle = '#222';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw Food
    ctx.fillStyle = '#e74c3c';
    ctx.fillRect(food.x * GRID_SIZE, food.y * GRID_SIZE, GRID_SIZE - 2, GRID_SIZE - 2);

    // Draw Snake
    ctx.fillStyle = '#4CAF50';
    for (let i = 0; i < snake.length; i++) {
        // Head is slightly different color
        if (i === 0) ctx.fillStyle = '#81C784';
        else ctx.fillStyle = '#4CAF50';
        
        ctx.fillRect(snake[i].x * GRID_SIZE, snake[i].y * GRID_SIZE, GRID_SIZE - 2, GRID_SIZE - 2);
    }
}

// Game Over
function gameOver() {
    isGameRunning = false;
    clearInterval(gameInterval);
    finalScoreDisplay.textContent = score;
    gameOverModal.classList.remove('hidden');
    startBtn.disabled = false;
    pauseBtn.disabled = true;
    speedSelect.disabled = false;
}

// Input Handling
document.addEventListener('keydown', (e) => {
    if (!isGameRunning || isPaused || changingDirection) return;

    switch (e.key) {
        case 'ArrowUp':
            if (dy === 0) { dx = 0; dy = -1; changingDirection = true; }
            break;
        case 'ArrowDown':
            if (dy === 0) { dx = 0; dy = 1; changingDirection = true; }
            break;
        case 'ArrowLeft':
            if (dx === 0) { dx = -1; dy = 0; changingDirection = true; }
            break;
        case 'ArrowRight':
            if (dx === 0) { dx = 1; dy = 0; changingDirection = true; }
            break;
    }
});

// Controls
startBtn.addEventListener('click', () => {
    if (isGameRunning) return;
    
    isGameRunning = true;
    isPaused = false;
    startBtn.disabled = true;
    pauseBtn.disabled = false;
    speedSelect.disabled = true;
    pauseBtn.textContent = '暫停';
    
    initGame();
    
    gameSpeed = parseInt(speedSelect.value);
    if (gameInterval) clearInterval(gameInterval);
    gameInterval = setInterval(gameLoop, gameSpeed);
});

// Dynamic Speed Adjustment
speedSelect.addEventListener('change', () => {
    gameSpeed = parseInt(speedSelect.value);
    if (isGameRunning && !isPaused) {
        clearInterval(gameInterval);
        gameInterval = setInterval(gameLoop, gameSpeed);
    }
});

pauseBtn.addEventListener('click', () => {
    if (!isGameRunning) return;

    isPaused = !isPaused;
    if (isPaused) {
        pauseBtn.textContent = '繼續';
    } else {
        pauseBtn.textContent = '暫停';
    }
});

restartBtn.addEventListener('click', () => {
    gameOverModal.classList.add('hidden');
    // Trigger start button click to restart
    startBtn.disabled = false; // Enable it momentarily so we can click it programmatically or just reset state
    startBtn.click();
});

// Initial Draw
initGame();
// Disable pause button initially
pauseBtn.disabled = true;