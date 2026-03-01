#include <windows.h>
#include <mmsystem.h>
#include <iostream>
#include <vector>
#include <string>
#include <chrono>
#include <thread>
#include <cstdlib>
#include <fstream>
#include <sstream>
#include <conio.h>
#include <algorithm>
#include <io.h>  // For _findfirst, _findnext (Windows directory listing)
#include <cstddef>

using namespace std;

// ==================== CONFIGURATION ====================
const string SONGS_FOLDER = "songs";
const string LYRICS_FOLDER = "lyrics";
const string CONVERTED_FOLDER = "converted";

// ==================== STRUCTURES ====================
struct Song {
    string name;
    string mp3Path;
    string wavPath;
    string lyricPath;
};

struct LyricLine {
    int time_ms;
    string text;
};

// ==================== UTILITY FUNCTIONS ====================
void setCursor(int x, int y) {
    COORD pos = { static_cast<SHORT>(x), static_cast<SHORT>(y) };
    SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
}

void setColor(int color) {
    SetConsoleTextAttribute(GetStdHandle(STD_OUTPUT_HANDLE), color);
}

void hideCursor() {
    CONSOLE_CURSOR_INFO cursorInfo;
    GetConsoleCursorInfo(GetStdHandle(STD_OUTPUT_HANDLE), &cursorInfo);
    cursorInfo.bVisible = FALSE;
    SetConsoleCursorInfo(GetStdHandle(STD_OUTPUT_HANDLE), &cursorInfo);
}

void showCursor() {
    CONSOLE_CURSOR_INFO cursorInfo;
    GetConsoleCursorInfo(GetStdHandle(STD_OUTPUT_HANDLE), &cursorInfo);
    cursorInfo.bVisible = TRUE;
    SetConsoleCursorInfo(GetStdHandle(STD_OUTPUT_HANDLE), &cursorInfo);
}

void clearScreen() {
    system("cls");
}

void centerText(int y, string text, int color) {
    CONSOLE_SCREEN_BUFFER_INFO csbi;
    GetConsoleScreenBufferInfo(GetStdHandle(STD_OUTPUT_HANDLE), &csbi);
    int width = csbi.srWindow.Right - csbi.srWindow.Left + 1;
    int x = max(0, (width - (int)text.length()) / 2);
    setCursor(x, y);
    setColor(color);
    cout << text;
}

// ==================== FILE MANAGEMENT ====================
void createFolders() {
    // Create necessary folders
    system("mkdir songs 2>nul");
    system("mkdir lyrics 2>nul");
    system("mkdir converted 2>nul");
}

vector<Song> getAvailableSongs() {
    vector<Song> songs;

    // Windows directory listing using _findfirst/_findnext
    struct _finddata_t fileinfo;
    intptr_t handle;
    string searchPath = SONGS_FOLDER + "/*.mp3";

    handle = _findfirst(searchPath.c_str(), &fileinfo);
    if (handle != -1) {
        do {
            if (!(fileinfo.attrib & _A_SUBDIR)) {
                string filename = fileinfo.name;

                Song song;
                song.name = filename.substr(0, filename.find_last_of("."));
                transform(song.name.begin(), song.name.end(), song.name.begin(), ::toupper);

                song.mp3Path = SONGS_FOLDER + "/" + filename;
                song.wavPath = CONVERTED_FOLDER + "/" + song.name + ".wav";
                song.lyricPath = LYRICS_FOLDER + "/" + song.name + ".txt";

                songs.push_back(song);
            }
        } while (_findnext(handle, &fileinfo) == 0);
        _findclose(handle);
    }

    return songs;
}

bool convertMP3toWAV(const string& mp3Path, const string& wavPath) {
    // Check if already converted
    ifstream test(wavPath);
    if (test.good()) {
        test.close();
        return true;
    }

    // Try to convert using ffmpeg
    string command = "ffmpeg -i \"" + mp3Path + "\" -acodec pcm_s16le -ar 44100 \"" + wavPath + "\" -y 2>nul";
    int result = system(command.c_str());

    // If ffmpeg fails, try using Windows built-in conversion
    if (result != 0) {
        // Alternative: Copy MP3 as WAV (will play but might have issues)
        command = "copy \"" + mp3Path + "\" \"" + wavPath + "\" >nul";
        system(command.c_str());
    }

    // Check if conversion succeeded
    ifstream check(wavPath);
    bool success = check.good();
    check.close();

    return success;
}

// ==================== LYRICS PARSING ====================
vector<LyricLine> loadLyrics(const string& lyricPath) {
    vector<LyricLine> lyrics;
    
    // Try to load lyrics from file first
    ifstream file(lyricPath);
    if (file.is_open()) {
        string line;
        while (getline(file, line)) {
            // Remove carriage return if present
            if (!line.empty() && line.back() == '\r') {
                line.pop_back();
            }
            
            size_t pipePos = line.find('|');
            if (pipePos != string::npos) {
                try {
                    int time = stoi(line.substr(0, pipePos));
                    string text = line.substr(pipePos + 1);
                    // Remove leading/trailing whitespace
                    text.erase(0, text.find_first_not_of(" \t\r\n"));
                    text.erase(text.find_last_not_of(" \t\r\n") + 1);
                    
                    if (!text.empty()) {
                        lyrics.push_back({time, text});
                    }
                } catch (...) {
                    // Skip invalid lines
                }
            }
        }
        file.close();
        
        // Sort lyrics by time (just in case)
        sort(lyrics.begin(), lyrics.end(), [](const LyricLine& a, const LyricLine& b) {
            return a.time_ms < b.time_ms;
        });
        
        return lyrics;
    }
    
    // If no lyrics file found, return empty
    return lyrics;
}

// ==================== CHRISTMAS TREE GUI ====================
void drawChristmasTree(int frame, int x, int y) {
    // BIG Christmas tree - properly aligned
    vector<string> treeLayers = {
        "            *            ",
        "           ooo           ",
        "          ooooo          ",
        "         ooooooo         ",
        "        ooooooooo        ",
        "       ooooooooooo       ",
        "      ooooooooooooo      ",
        "     ooooooooooooooo     ",
        "    ooooooooooooooooo    ",
        "   ooooooooooooooooooo   ",
        "  ooooooooooooooooooooo  ",
        " ooooooooooooooooooooooo ",
        "         HHHHHHH         ",
        "         HHHHHHH         ",
        "         HHHHHHH         "
    };

    // Color cycling for lights
    int lightColors[] = {
        12, // Red
        14, // Yellow
        10, // Green
        11, // Cyan
        13, // Magenta
        9   // Blue
    };

    for (size_t i = 0; i < treeLayers.size(); i++) {
        setCursor(x, y + i);
        
        string layer = treeLayers[i];
        for (size_t j = 0; j < layer.length(); j++) {
            char c = layer[j];
            
            if (c == 'o') {
                // Animated lights
                int colorIndex = (frame + i * 3 + j) % 6;
                setColor(lightColors[colorIndex]);
                cout << 'o';
            }
            else if (c == 'H') {
                // Tree trunk
                setColor(6); // Brown
                cout << 'H';
            }
            else if (c == '*') {
                // Star at top
                int starColor = 14; // Yellow
                if ((frame / 5) % 2 == 0) starColor = 15; // Bright white for blinking
                setColor(starColor);
                cout << '+';
            }
            else if (c == ' ') {
                // Empty space - different shades of green for tree
                int greenLevel = 2 + ((i + j + frame/10) % 4);
                setColor(greenLevel);
                cout << ' ';
            }
        }
    }
}

void drawProgressBar(int x, int y, int width, float progress, int color) {
    setCursor(x, y);
    setColor(color);
    cout << "[";
    
    int filled = (int)((width - 2) * progress);
    for (int i = 0; i < width - 2; i++) {
        if (i < filled) {
            setColor(color);
            cout << "#";
        } else {
            setColor(8);
            cout << "-";
        }
    }
    setColor(color);
    cout << "]";
}

// ==================== SIMPLE MUSIC PLAYER ====================
void PlaySoundFile(const string& filepath, bool async = true) {
    if (async) {
        PlaySound(filepath.c_str(), NULL, SND_FILENAME | SND_ASYNC);
    } else {
        PlaySound(filepath.c_str(), NULL, SND_FILENAME);
    }
}

void StopSound() {
    PlaySound(NULL, 0, 0);
}

// ==================== MAIN MENU ====================
int showMainMenu(const vector<Song>& songs) {
    clearScreen();

    // Draw title with Christmas colors
    centerText(1, "*** CHRISTMAS MUSIC PLAYER ***", 13);
    centerText(2, "==============================", 10);
    
    // Draw a small tree on the side
    vector<string> miniTree = {
        "   *   ",
        "  ooo  ",
        " ooooo ",
        "ooooooo",
        "  HHH  "
    };
    
    for (size_t i = 0; i < miniTree.size(); i++) {
        setCursor(5, 4 + i);
        setColor(10 + (i % 3));
        cout << miniTree[i];
    }
    
    // Song list title
    centerText(4, "=== AVAILABLE SONGS ===", 14);

    // Draw song list
    int startY = 6;
    for (size_t i = 0; i < songs.size(); i++) {
        // Check if lyrics exist
        ifstream lyricFile(songs[i].lyricPath.c_str());
        bool hasLyrics = lyricFile.good();
        lyricFile.close();
        
        // Draw selection number
        setCursor(15, startY + i);
        setColor(11);
        cout << "[" << (i + 1) << "] ";
        
        // Draw song name
        setColor(15);
        cout << songs[i].name;
        
        // Show lyrics indicator
        if (hasLyrics) {
            setColor(10);
            cout << " [LYRICS]";
        }
    }

    // Draw instructions at bottom
    centerText(startY + (int)songs.size() + 2, "------------------------------", 8);
    centerText(startY + (int)songs.size() + 3, "1-" + to_string(songs.size()) + ": Select Song", 7);
    centerText(startY + (int)songs.size() + 4, "C: Convert MP3 to WAV  |  ESC: Exit", 7);

    // Wait for selection
    while (true) {
        if (_kbhit()) {
            char ch = _getch();

            // Number selection
            if (ch >= '1' && ch <= '9') {
                int index = ch - '1';
                if (index < (int)songs.size()) {
                    return index;
                }
            }
            // Convert command
            else if (ch == 'c' || ch == 'C') {
                return -2; // Convert signal
            }
            // Exit
            else if (ch == 27) {
                return -1;
            }
        }
        this_thread::sleep_for(chrono::milliseconds(100));
    }
}

// ==================== MUSIC PLAYER SCREEN ====================
void playSong(const Song& song) {
    clearScreen();
    hideCursor();

    // Load lyrics
    vector<LyricLine> lyrics = loadLyrics(song.lyricPath);
    
    // Display message if no lyrics
    if (lyrics.empty()) {
        lyrics.push_back({0, "No lyrics found for: " + song.name});
        lyrics.push_back({5000, "Lyrics should be in: " + LYRICS_FOLDER + "/" + song.name + ".txt"});
        lyrics.push_back({10000, "Format: TIMESTAMP|LYRIC_TEXT"});
        lyrics.push_back({15000, "Example: 13000|Last Christmas, I gave you my heart"});
    }

    // Try to convert and play
    bool converted = convertMP3toWAV(song.mp3Path, song.wavPath);
    bool musicPlaying = false;

    if (converted) {
        PlaySoundFile(song.wavPath, true);
        musicPlaying = true;
    }

    // Draw title
    centerText(1, "=== NOW PLAYING ===", 14);
    centerText(2, song.name, 15);
    
    // Draw a line separator
    centerText(3, "==============================", 10);

    // Draw BIG Christmas tree on the left side - properly centered
    int treeX = 10;  // More centered position
    int treeY = 5;
    drawChristmasTree(0, treeX, treeY);

    // Display music status BELOW the tree
    setCursor(treeX + 5, treeY + 16);
    setColor(14);
    cout << "STATUS: ";
    if (musicPlaying) {
        setColor(10);
        cout << "> PLAYING";
    } else if (converted) {
        setColor(12);
        cout << "X ERROR";
    } else {
        setColor(14);
        cout << "... CONVERTING...";
    }

    // Draw lyrics section BESIDE the tree (on the right)
    int lyricsX = treeX + 28; // Better spacing
    int lyricsY = treeY;
    const int MAX_LYRICS_DISPLAY = 7; // How many lyrics to show at once
    const int LYRIC_LINE_WIDTH = 40; // Width for each lyric line
    
    // Draw lyrics header
    setCursor(lyricsX, lyricsY);
    setColor(11);
    cout << "--- LYRICS ---";
    
    // Draw a line under lyrics header
    setCursor(lyricsX, lyricsY + 1);
    setColor(8);
    for (int i = 0; i < 20; i++) cout << "-"; // Longer line

    // Clear the entire lyrics area initially
    for (int line = 0; line < MAX_LYRICS_DISPLAY + 2; line++) {
        setCursor(lyricsX, lyricsY + 2 + line);
        for (int i = 0; i < LYRIC_LINE_WIDTH; i++) {
            cout << " ";
        }
    }

    // Player loop
    bool running = true;
    bool paused = false;
    int frame = 0;
    size_t currentLyric = 0;
    vector<string> displayedLyrics; // Store last few lyrics
    bool lyricsInitialized = false;

    auto startTime = chrono::steady_clock::now();
    auto pauseStartTime = startTime;
    chrono::milliseconds pauseDuration = chrono::milliseconds(0);

    while (running) {
        // Handle input
        if (_kbhit()) {
            char ch = _getch();
            if (ch == 27) { // ESC
                running = false;
            }
            else if (ch == 32) { // SPACE
                paused = !paused;
                if (paused) {
                    pauseStartTime = chrono::steady_clock::now();
                    StopSound();
                    
                    // Update status
                    setCursor(treeX + 13, treeY + 16);
                    setColor(12);
                    cout << "|| PAUSED ";
                } else {
                    pauseDuration += chrono::duration_cast<chrono::milliseconds>(
                        chrono::steady_clock::now() - pauseStartTime);
                    
                    if (musicPlaying) {
                        PlaySoundFile(song.wavPath, true);
                    }
                    
                    // Update status
                    setCursor(treeX + 13, treeY + 16);
                    setColor(10);
                    cout << "> PLAYING ";
                }
            }
        }

        if (!paused) {
            // Update time
            auto currentTime = chrono::steady_clock::now();
            auto elapsed = chrono::duration_cast<chrono::milliseconds>(
                currentTime - startTime - pauseDuration);

            // Update animation frame
            frame++;
            drawChristmasTree(frame, treeX, treeY);

            // Update progress bar BELOW the tree
            float progress = 0.0f;
            if (!lyrics.empty() && lyrics.back().time_ms > 0) {
                progress = min(1.0f, (float)elapsed.count() / max(lyrics.back().time_ms, 180000));
            }
            
            // Draw progress bar below tree and status
            setCursor(treeX, treeY + 18);
            setColor(7);
            cout << "Progress: ";
            drawProgressBar(treeX + 9, treeY + 18, 25, progress, 11);

            // Display current time below progress bar
            setCursor(treeX, treeY + 19);
            setColor(7);
            int totalSeconds = (int)elapsed.count() / 1000;
            int minutes = totalSeconds / 60;
            int seconds = totalSeconds % 60;
            cout << "Time: " << minutes << ":" << (seconds < 10 ? "0" : "") << seconds;
            
            // Display lyrics counter
            setCursor(treeX + 20, treeY + 19);
            setColor(7);
            cout << "Lyric: " << (currentLyric + 1) << "/" << lyrics.size();

            // Display lyrics BESIDE the tree
            if (!lyrics.empty()) {
                // Find current lyric based on time
                size_t lyricIndex = 0;
                for (size_t i = 0; i < lyrics.size(); i++) {
                    if (elapsed.count() >= lyrics[i].time_ms) {
                        lyricIndex = i;
                    } else {
                        break;
                    }
                }
                
                // Update if we have a new lyric or need to initialize
                if (lyricIndex != currentLyric || !lyricsInitialized) {
                    currentLyric = lyricIndex;
                    lyricsInitialized = true;
                    displayedLyrics.clear();
                    
                    // Store lyrics around current lyric (3 before, 3 after)
                    int startIdx = max(0, (int)currentLyric - 3);
                    int endIdx = min((int)lyrics.size(), (int)currentLyric + 4); // Show 3 after
                    
                    // Clear all lyric lines first
                    for (int line = 0; line < MAX_LYRICS_DISPLAY; line++) {
                        int linePos = lyricsY + 3 + line;
                        setCursor(lyricsX, linePos);
                        for (int j = 0; j < LYRIC_LINE_WIDTH; j++) {
                            cout << " ";
                        }
                    }
                    
                    // Now display the new lyrics
                    for (int i = startIdx; i < endIdx && (i - startIdx) < MAX_LYRICS_DISPLAY; i++) {
                        int displayLine = lyricsY + 3 + (i - startIdx);
                        
                        // Clear the line
                        setCursor(lyricsX, displayLine);
                        for (int j = 0; j < LYRIC_LINE_WIDTH; j++) {
                            cout << " ";
                        }
                        
                        // Set cursor and color
                        setCursor(lyricsX, displayLine);
                        
                        if (i == (int)currentLyric) {
                            // Current line - highlight it
                            setColor(14); // Bright yellow
                            cout << "> ";
                        } else {
                            // Other lines
                            setColor(8); // Gray
                            cout << "  ";
                        }
                        
                        // Display the lyric text
                        string lyricText = lyrics[i].text;
                        
                        // Truncate if too long
                        int maxTextWidth = LYRIC_LINE_WIDTH - 4; // Subtract 2 for "> " or "  "
                        if (lyricText.length() > maxTextWidth) {
                            // Show beginning and add ellipsis
                            cout << lyricText.substr(0, maxTextWidth - 3) << "...";
                        } else {
                            // Show full text
                            cout << lyricText;
                            // Fill with spaces to clear any leftover text
                            int spacesNeeded = maxTextWidth - lyricText.length();
                            for (int j = 0; j < spacesNeeded; j++) {
                                cout << " ";
                            }
                        }
                    }
                    
                    // Clear any remaining lines that might have old content
                    int linesUsed = min(MAX_LYRICS_DISPLAY, endIdx - startIdx);
                    for (int line = linesUsed; line < MAX_LYRICS_DISPLAY; line++) {
                        int linePos = lyricsY + 3 + line;
                        setCursor(lyricsX, linePos);
                        for (int j = 0; j < LYRIC_LINE_WIDTH; j++) {
                            cout << " ";
                        }
                    }
                }
            }
            
            // Draw controls at bottom
            centerText(25, "[ESC] Back  [SPACE] " + string(paused ? "Resume" : "Pause"), 7);
        }

        this_thread::sleep_for(chrono::milliseconds(50)); // 20 FPS
    }

    // Stop music
    StopSound();
    showCursor();
}

// ==================== CONVERSION SCREEN ====================
void showConversionScreen(const vector<Song>& songs) {
    clearScreen();

    centerText(2, "=== CONVERTING MP3 TO WAV ===", 13);
    centerText(3, "-----------------------------", 10);

    int y = 6;
    for (size_t i = 0; i < songs.size(); i++) {
        setCursor(20, y + i);
        setColor(15);
        cout << songs[i].name;
        
        setCursor(45, y + i);
        cout << "... ";

        // Check if already converted
        ifstream test(songs[i].wavPath.c_str());
        if (test.good()) {
            setColor(10);
            cout << "[READY]";
        } else {
            // Convert
            setColor(14);
            cout << "[CONVERTING]";
            cout.flush();

            bool success = convertMP3toWAV(songs[i].mp3Path, songs[i].wavPath);

            setCursor(45, y + i);
            if (success) {
                setColor(10);
                cout << "[DONE]    ";
            } else {
                setColor(12);
                cout << "[FAILED]  ";
            }
        }
    }

    centerText(y + (int)songs.size() + 2, "-----------------------------", 8);
    centerText(y + (int)songs.size() + 3, "Press any key to continue...", 11);
    _getch();
}

// ==================== WELCOME SCREEN ====================
void showWelcomeScreen() {
    clearScreen();

    // Big animated Christmas tree
    vector<string> bigTree = {
        "            *            ",
        "           ooo           ",
        "          ooooo          ",
        "         ooooooo         ",
        "        ooooooooo        ",
        "       ooooooooooo       ",
        "      ooooooooooooo      ",
        "     ooooooooooooooo     ",
        "    ooooooooooooooooo    ",
        "   ooooooooooooooooooo   ",
        "  ooooooooooooooooooooo  ",
        " ooooooooooooooooooooooo ",
        "         HHHHHHH         ",
        "         HHHHHHH         ",
        "         HHHHHHH         "
    };

    // Draw animated welcome screen
    for (int frame = 0; frame < 30; frame++) {
        clearScreen();

        // Title with animation
        centerText(2, "*** CHRISTMAS MUSIC PLAYER ***", 13 + (frame % 2));
        
        // Draw animated tree
        for (size_t i = 0; i < bigTree.size(); i++) {
            centerText(5 + i, bigTree[i], 10 + ((frame + i) % 6));
        }

        // Instructions with blinking effect
        if (frame % 10 < 7) {
            centerText(20, "Place MP3 files in 'songs' folder", 7);
            centerText(21, "Place lyrics in 'lyrics' folder (TIMESTAMP|LYRICS)", 7);
            centerText(22, "Enjoy your Christmas music!", 14);
        }

        // Loading animation
        string dots = ".";
        for (int i = 0; i < frame % 4; i++) dots += ".";
        centerText(24, "Loading" + dots, 11);

        this_thread::sleep_for(chrono::milliseconds(150));
    }

    centerText(24, "Press any key to continue...", 11);
    _getch();
}

// ==================== MAIN FUNCTION ====================
int main() {
    // Setup
    createFolders();
    showWelcomeScreen();

    // Main program loop
    while (true) {
        // Get available songs
        vector<Song> songs = getAvailableSongs();

        if (songs.empty()) {
            clearScreen();
            centerText(10, "!!! No MP3 files found in 'songs' folder!", 12);
            centerText(12, "Please add some MP3 files and restart.", 14);
            centerText(14, "Press any key to exit...", 7);
            _getch();
            break;
        }

        // Show menu
        int choice = showMainMenu(songs);

        if (choice == -1) { // Exit
            break;
        }
        else if (choice == -2) { // Convert
            showConversionScreen(songs);
        }
        else if (choice >= 0 && choice < (int)songs.size()) { // Play song
            playSong(songs[choice]);
        }
    }

    // Goodbye
    clearScreen();
    centerText(10, " *** MERRY CHRISTMAS! *** ", 12);
    centerText(12, "Thanks for using Christmas Music Player", 14);
    centerText(14, "Press any key to exit...", 7);
    _getch();

    return 0;
}