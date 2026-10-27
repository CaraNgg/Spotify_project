
function showTab(tabId, button){
    document.querySelectorAll(".tab").forEach(tab => tab.classList.add("hidden"));
    document.getElementById(tabId).classList.remove("hidden");

    document.querySelectorAll("nav button").forEach(btn => btn.classList.remove("active"));
    button.classList.add("active");

}

//adding the pyodide shit?
let pyodide;

async function setup(){
    const status = document.getElementById("status");
    status.textContent = "Loading, please wait a few seconds..."; //tells user to wait for a sec

    pyodide = await loadPyodide(); //start python in browser
    await pyodide.loadPackage(["pandas", "tzdata"]); //load the python libraries needed (pandas and tzdata(toronto timezone)

    // copy my python files into pyodide so python can import them
    const files = ["spotify_loading.py", "songs_tab.py", "main.py"];
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
    const nameA = document.getElementById("nameA").value || "Person 1";
    const nameB = document.getElementById("nameB").value || "Person 2";

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

    const songs = JSON.parse(main.get_songs(nameA, nameB)); //turns JSON text into a javascript object
    showSongs(songs, nameA, nameB); //to show the songs (FUNCTION IS BELOW)

    status.textContent = "Done!";
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

document.getElementById("loadBtn").addEventListener("click", compare);


setup(); //run setup as soon as page opens, so python is ready as soon as they click compare