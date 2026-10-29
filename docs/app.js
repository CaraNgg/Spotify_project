//to show the initial tabs on the side
function showTab(tabId, button){
    document.querySelectorAll(".tab").forEach(tab => tab.classList.add("hidden"));
    document.getElementById(tabId).classList.remove("hidden");

    document.querySelectorAll("nav button").forEach(btn => btn.classList.remove("active")); //select all buttons in the nav
    button.classList.add("active");

}

//to show the individual and shared song tabs on the SONGS TAB
function showSongView(viewId, button) {
    document.querySelectorAll(".song-view").forEach(view => view.classList.add("hidden"));
    document.getElementById(viewId).classList.remove("hidden");

    document.querySelectorAll("#songs button").forEach(btn => btn.classList.remove("active")); //select all buttons in the element with id songs
    button.classList.add("active");
}

//to show the individual and shared artist tabs on the ARTIST TAB
function showArtistView(viewId, button) {
    document.querySelectorAll(".artist-view").forEach(view => view.classList.add("hidden"));
    document.getElementById(viewId).classList.remove("hidden");

    document.querySelectorAll("#artists button").forEach(btn => btn.classList.remove("active")); //select all buttons in the element with id songs
    button.classList.add("active");
}

//adding the pyodide shit?
let pyodide;
let nameA, nameB;

async function setup(){
    const status = document.getElementById("status");
    status.textContent = "Loading, please wait a few seconds..."; //tells user to wait for a sec

    pyodide = await loadPyodide(); //start python in browser
    await pyodide.loadPackage(["pandas", "tzdata"]); //load the python libraries needed (pandas and tzdata(toronto timezone)

    // copy my python files into pyodide so python can import them
    const files = ["spotify_loading.py", "songs_tab.py", "artists_tab.py", "main.py", "blend_funny_tab.py"];
    for (const file of files) {
        const response = await fetch(file);          // download the file from my site
        const code = await response.text();          // get its contents as text
        pyodide.FS.writeFile(file, code);            // save it inside pyodide's file system
    }
    pyodide.runPython("import main"); // test that python can import them

    status.textContent = "Ready! Upload both zips."; //tells user they can upload their zips now
}

//runs once i click on "compare"
async function compare() {
    const status = document.getElementById("status");

    // get what the user picked
    const fileA = document.getElementById("zipA").files[0];
    const fileB = document.getElementById("zipB").files[0];
    nameA = document.getElementById("nameA").value || "Person 1";
    nameB = document.getElementById("nameB").value || "Person 2";

    if (!fileA || !fileB) {
        status.textContent = "Please choose both zip files.";
        return;
    }

    status.textContent = "Crunching your listening history...";
    await new Promise(r => setTimeout(r, 0));   // let the message show before the heavy work

    // save both zips into pyodide's file system
    pyodide.FS.writeFile("/a.zip", new Uint8Array(await fileA.arrayBuffer()));
    pyodide.FS.writeFile("/b.zip", new Uint8Array(await fileB.arrayBuffer()));

    // run load_both from main.py
    const main = pyodide.pyimport("main");
    main.load_both(nameA, nameB); //runs the python function, which returns JSON text

    //====================================================================================================
    //update through window
    updateSongs();

    updateArtists();

    fillArtistList();

    //for blend funny
    const game = JSON.parse(main.get_game(nameA, nameB));
    showGame(game);

    //====================================================================================================

    status.textContent = "Done!";
}

//for the window feature, to update the song shit every time a window is changed in the SONGS TAB
function updateSongs() {
    const timeWindow = document.getElementById("songsWindow").value;   // "all", "12m", or "6m"
    const main = pyodide.pyimport("main");

    const songs = JSON.parse(main.get_songs(nameA, nameB, timeWindow));
    showSongs(songs, nameA, nameB);

    const sharedSongs = JSON.parse(main.get_shared_songs(nameA, nameB, timeWindow));
    showSharedSongs(sharedSongs, nameA, nameB);
}

//build the table queen
function showSongs(songs, nameA, nameB) {
    let html = '<div class="side-by-side">';   // container for both columns

    for (const name of [nameA, nameB]) {
        html += '<div class="song-column">';    // one box per person
        html += `<h3>${name}'s top songs</h3>`;
        html += "<table><tr><th>#</th><th>Song</th><th>Artist</th><th>Plays</th></tr>";

        songs[name].forEach((row, i) => {
            html += `<tr><td>${i + 1}</td><td>${row.track}</td><td>${row.artist}</td><td>${row[name + "_plays"]}</td></tr>`;
        });

        html += "</table>";
        html += "</div>";                         // close this person's box
    }

    html += "</div>";                             // close the container
    document.getElementById("songsOutput").innerHTML = html;
}

function showSharedSongs(sharedSongs, nameA, nameB){
    let html = "<table>";

    // header row
    html += `<tr><th>#</th><th>Song</th><th>Artist</th><th>${nameA}'s plays</th><th>${nameB}'s plays</th></tr>`;

    // one row per shared song
    sharedSongs.forEach((row, i) => {
        html += `<tr>
            <td>${i + 1}</td>
            <td>${row.track}</td>
            <td>${row.artist}</td>
            <td>${row[nameA + "_plays"]}</td>
            <td>${row[nameB + "_plays"]}</td>
        </tr>`;
    });

    html += "</table>";
    document.getElementById("sharedSongsOutput").innerHTML = html;
}


//for the window feature, to update the song shit every time a window is changed in the SONGS TAB
function updateArtists() {
    const timeWindow = document.getElementById("artistsWindow").value;   // "all", "12m", or "6m"
    const main = pyodide.pyimport("main");

    const artists = JSON.parse(main.get_artists(nameA, nameB, timeWindow));
    showArtists(artists, nameA, nameB);

    const sharedArtists = JSON.parse(main.get_shared_artists(nameA, nameB, timeWindow));
    showSharedArtists(sharedArtists, nameA, nameB);
}

function showArtists(artists, nameA, nameB) {
    let html = '<div class="side-by-side">';   // container for both columns

    for (const name of [nameA, nameB]) {
        html += '<div class="artist-column">';    // one box per person
        html += `<h3>${name}'s top artists</h3>`;
        html += "<table><tr><th>#</th><th>Artist</th><th>Hours</th></tr>";

        artists[name].forEach((row, i) => {
            html += `<tr><td>${i + 1}</td><td>${row.artist}</td><td>${row[name + "_hours"].toFixed(1)}</td></tr>`;
        });

        html += "</table>";
        html += "</div>";                         // close this person's box
    }

    html += "</div>";                             // close the container
    document.getElementById("artistsOutput").innerHTML = html;
}

function showSharedArtists(sharedArtists, nameA, nameB){
    let html = "<table>";

    // header row
    html += `<tr><th>#</th><th>Artist</th><th>${nameA}'s hours</th><th>${nameB}'s hours</th></tr>`;

    // one row per shared artist
    sharedArtists.forEach((row, i) => {
        html += `<tr>
            <td>${i + 1}</td>
            <td>${row.artist}</td>
            <td>${row[nameA + "_hours"].toFixed(1)}</td>
            <td>${row[nameB + "_hours"].toFixed(1)}</td>
        </tr>`;
    });

    html += "</table>";
    document.getElementById("sharedArtistsOutput").innerHTML = html;
}

//to suggest shit as they type it up
function fillArtistList() {
    const main = pyodide.pyimport("main");
    const artistNames = JSON.parse(main.get_all_artists());   // ["Artist X", "Artist Y", ...]

    let html = "";
    artistNames.forEach(name => {
        html += `<option value="${name}">`;
    });

    document.getElementById("artistList").innerHTML = html;
}

//run the artist search
function searchArtist() {
    if (!nameA) return;   // no data loaded yet, so do nothing

    const artistName = document.getElementById("artistName").value;
    const main = pyodide.pyimport("main");
    const report = JSON.parse(main.get_artist_report(nameA, nameB, artistName));

    if (report === null) {
        document.getElementById("artistReportOutput").innerHTML =
            `<p>Neither of you has listened to "${artistName}".</p>`;
        return;
    }

    showArtistReport(report);
}

//build artist page
function showArtistReport(report) {
    let html = `<h3>${report.artist}</h3>`;
    html += '<div class="side-by-side">';

    // one column per person
    for (const name of [nameA, nameB]) {
        const stats = report[name];
        html += '<div class="song-column">';
        html += `<h4>${name}</h4>`;

        if (stats === null) {
            html += `<p>${name} has never listened to this artist.</p>`;
        } else {
            html += `<p>First listened: ${stats.first_date.slice(0, 10)}</p>`;
            html += `<p>First song: ${stats.first_song}</p>`;
            html += `<p>Hours: ${stats.hours.toFixed(1)}</p>`;
            html += `<p>Rank: #${stats.rank}</p>`;

            html += "<p>Top songs:</p><ol>";
            for (const [song, plays] of Object.entries(stats.top_songs)) {
                html += `<li>${song} (${plays} plays)</li>`;
            }
            html += "</ol>";
        }
        html += "</div>";
    }
    html += "</div>";

    // comparisons, only if both listened
    if (report.listened_first) {
        html += `<p>🎧 ${report.listened_first} listened first, by ${report.gap_days} days</p>`;
        html += `<p>🏆 Bigger fan: ${report.bigger_fan}</p>`;
    }

    document.getElementById("artistReportOutput").innerHTML = html;
}

//idek for the game to show
function showGame(questions) {
    let html = "";

    questions.forEach(q => {
        html += `<h3>${q.title}</h3>`;

        // optional info card (always visible, not clickable)
        if (q.info) {
            html += `<div class="info-card">
                <p class="answer-main">${q.info.main}</p>
                <p class="answer-detail">${q.info.detail}</p>
            </div>`;
        }

        html += '<div class="side-by-side">';

        q.cards.forEach(card => {
            html += `<div class="reveal-card" onclick="this.classList.add('revealed')">
                <p>${card.prompt}</p>
                <p class="hint">Click to reveal</p>
                <div class="answer">
                    <p class="answer-main">${card.answer}</p>
                    <p class="answer-detail">${card.detail}</p>
                </div>
            </div>`;
        });

        html += "</div>";
    });

    document.getElementById("gameOutput").innerHTML = html;
}

document.getElementById("loadBtn").addEventListener("click", compare);

//whenever someone picks another window option, refresh the song tables
document.getElementById("songsWindow").addEventListener("change", () => {
    if (nameA) updateSongs();
});

//whenever picks another window, refresh the artist windows
document.getElementById("artistsWindow").addEventListener("change", () => {
    if (nameA) updateArtists();
});

//runs search when the search button is clicked
document.getElementById("searchArtistButton").addEventListener("click", searchArtist);

//runs search when enter button is clicked
document.getElementById("artistName").addEventListener("keydown", (event) => {
    if (event.key === "Enter") searchArtist();
});

setup(); //run setup as soon as page opens, so python is ready as soon as they click compare