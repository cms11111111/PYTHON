using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;

namespace SnakeConsole
{
    class Program
    {
        // 點結構，用來儲存座標
        struct Point
        {
            public int X { get; set; }
            public int Y { get; set; }
            public Point(int x, int y) { X = x; Y = y; }
        }

        // 遊戲設定
        const int GRID_SIZE = 20;
        static int SleepTime = 100; // 預設速度

        static void Main(string[] args)
        {
            Console.CursorVisible = false;
            Console.Title = "食蛇遊戲 (Snake Game)";

            while (true)
            {
                ShowMainMenu();
                PlayGame();
                
                // 遊戲結束後詢問是否重玩
                Console.SetCursorPosition(0, GRID_SIZE + 3);
                Console.ForegroundColor = ConsoleColor.White;
                Console.Write("Press Enter to Restart or Esc to Quit...");
                
                // 清空輸入緩衝
                while (Console.KeyAvailable) Console.ReadKey(true);

                bool restart = false;
                while (true)
                {
                    var key = Console.ReadKey(true).Key;
                    if (key == ConsoleKey.Enter) { restart = true; break; }
                    if (key == ConsoleKey.Escape) { restart = false; break; }
                }

                if (!restart) break;
            }
        }

        static void ShowMainMenu()
        {
            Console.Clear();
            Console.ForegroundColor = ConsoleColor.Green;
            Console.WriteLine("=== 食蛇遊戲 (Snake Game) ===");
            Console.ResetColor();
            Console.WriteLine();
            Console.WriteLine("1. 慢 (Slow) - 150ms");
            Console.WriteLine("2. 中 (Medium) - 100ms");
            Console.WriteLine("3. 快 (Fast) - 50ms");
            Console.WriteLine();
            Console.Write("請選擇速度 (1-3): ");

            while (true)
            {
                var key = Console.ReadKey(true).KeyChar;
                if (key == '1') { SleepTime = 150; break; }
                if (key == '2') { SleepTime = 100; break; }
                if (key == '3') { SleepTime = 50; break; }
            }
        }

        static void PlayGame()
        {
            // 使用 List<T> (泛型串列) 來管理蛇的身體
            // 泛型是物件導向程式語言常用的資料結構 (流浪貓之家)
            List<Point> snake = new List<Point>
            {
                new Point(10, 10),
                new Point(9, 10),
                new Point(8, 10)
            };

            Point food = SpawnFood(snake);
            Point direction = new Point(1, 0); // 初始向右移動
            Point nextDirection = direction;   // 防止單次 tick 多次轉向導致自殺
            int score = 0;
            bool gameOver = false;
            bool isPaused = false;

            Console.Clear();
            DrawWalls();
            DrawGame(snake, food, score, isPaused);

            // 遊戲主迴圈
            while (!gameOver)
            {
                // 輸入處理
                if (Console.KeyAvailable)
                {
                    var key = Console.ReadKey(true).Key;
                    switch (key)
                    {
                        case ConsoleKey.UpArrow: 
                            if (direction.Y == 0) nextDirection = new Point(0, -1); break;
                        case ConsoleKey.DownArrow: 
                            if (direction.Y == 0) nextDirection = new Point(0, 1); break;
                        case ConsoleKey.LeftArrow: 
                            if (direction.X == 0) nextDirection = new Point(-1, 0); break;
                        case ConsoleKey.RightArrow: 
                            if (direction.X == 0) nextDirection = new Point(1, 0); break;
                        case ConsoleKey.P:
                            isPaused = !isPaused;
                            DrawScoreBar(score, isPaused);
                            break;
                    }
                }

                if (isPaused)
                {
                    Thread.Sleep(100);
                    continue;
                }

                direction = nextDirection;

                // 計算新頭部位置
                Point head = snake[0];
                Point newHead = new Point(head.X + direction.X, head.Y + direction.Y);

                // 碰撞檢查 (牆壁)
                // 邏輯座標 0~(GRID_SIZE-1)
                if (newHead.X < 0 || newHead.X >= GRID_SIZE || newHead.Y < 0 || newHead.Y >= GRID_SIZE)
                {
                    gameOver = true;
                    break;
                }

                // 碰撞檢查 (自己)
                // 檢查是否撞到身體 (排除尾巴，因為如果不吃食物，尾巴會移動)
                // 但如果新頭部位置就是目前的尾巴位置(且沒吃到食物)，是安全的，因為尾巴會縮
                // 這裡簡化檢查：撞到身體任何部分就算死 (除非剛好追著尾巴跑，這裡稍微嚴格一點)
                if (snake.Take(snake.Count - 1).Any(p => p.X == newHead.X && p.Y == newHead.Y))
                {
                    gameOver = true;
                    break;
                }

                // 將新頭部加入 List<T> 的最前面 (Insert)
                snake.Insert(0, newHead);

                // 檢查是否吃到食物
                if (newHead.X == food.X && newHead.Y == food.Y)
                {
                    score += 10;
                    food = SpawnFood(snake);
                    // 吃到食物不移除尾巴 -> 變長
                    DrawPoint(food, ConsoleColor.Red); // 畫新食物
                }
                else
                {
                    // 沒吃到食物，移除尾巴 (RemoveAt)
                    Point tail = snake.Last();
                    ClearPoint(tail); // 清除畫面上的尾巴
                    snake.RemoveAt(snake.Count - 1);
                }

                // 繪製更新
                DrawPoint(newHead, ConsoleColor.Green);      // 新頭
                DrawPoint(snake[1], ConsoleColor.DarkGreen); // 舊頭變身體
                
                // 更新分數
                DrawScoreBar(score, isPaused);

                Thread.Sleep(SleepTime);
            }

            ShowGameOver(score);
        }

        static void DrawWalls()
        {
            Console.ForegroundColor = ConsoleColor.White;
            // 繪製上牆
            Console.SetCursorPosition(0, 0);
            Console.Write("+" + new string('-', GRID_SIZE * 2) + "+");
            
            // 繪製側牆
            for (int y = 0; y < GRID_SIZE; y++)
            {
                Console.SetCursorPosition(0, y + 1);
                Console.Write("|");
                Console.SetCursorPosition(GRID_SIZE * 2 + 1, y + 1);
                Console.Write("|");
            }

            // 繪製下牆
            Console.SetCursorPosition(0, GRID_SIZE + 1);
            Console.Write("+" + new string('-', GRID_SIZE * 2) + "+");
        }

        // 輔助繪圖：將邏輯座標 (x,y) 轉換為 Console 座標 (x*2+1, y+1)
        // 因為 Console 字元高長比約 2:1，所以 X 軸乘 2 看起來比較像正方形
        static void DrawPoint(Point p, ConsoleColor color)
        {
            Console.SetCursorPosition(p.X * 2 + 1, p.Y + 1);
            Console.ForegroundColor = color;
            Console.Write("[]"); // 使用 [] 代表一格
        }

        static void ClearPoint(Point p)
        {
            Console.SetCursorPosition(p.X * 2 + 1, p.Y + 1);
            Console.Write("  ");
        }

        static void DrawGame(List<Point> snake, Point food, int score, bool isPaused)
        {
            // 畫蛇
            for (int i = 0; i < snake.Count; i++)
            {
                DrawPoint(snake[i], i == 0 ? ConsoleColor.Green : ConsoleColor.DarkGreen);
            }

            // 畫食物
            DrawPoint(food, ConsoleColor.Red);

            // 顯示分數與狀態
            DrawScoreBar(score, isPaused);
        }

        static void DrawScoreBar(int score, bool isPaused)
        {
            Console.SetCursorPosition(0, GRID_SIZE + 1); // 蓋在下牆上? 不，下牆在 GRID_SIZE + 1
            // 調整到下牆下方
            Console.SetCursorPosition(0, GRID_SIZE + 2);
            Console.ForegroundColor = ConsoleColor.White;
            Console.Write($"Score: {score,-5} " + (isPaused ? "[PAUSED]       " : "Press 'P' Pause"));
        }

        static Point SpawnFood(List<Point> snake)
        {
            Random rnd = new Random();
            Point food;
            do
            {
                food = new Point(rnd.Next(0, GRID_SIZE), rnd.Next(0, GRID_SIZE));
            } while (snake.Any(p => p.X == food.X && p.Y == food.Y));
            return food;
        }

        static void ShowGameOver(int score)
        {
            int centerX = GRID_SIZE; // 實際上是 GRID_SIZE * 2 / 2
            int centerY = GRID_SIZE / 2;
            
            Console.ForegroundColor = ConsoleColor.Red;
            Console.SetCursorPosition(centerX * 2 - 4, centerY); // 大概置中
            Console.Write("GAME OVER!");
            Console.SetCursorPosition(centerX * 2 - 5, centerY + 1);
            Console.Write($"Final Score: {score}");
            Console.ResetColor();
        }
    }
}