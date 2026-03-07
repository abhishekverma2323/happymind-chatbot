const input = document.getElementById("input");
const chat = document.getElementById("chat");

input.focus();

input.addEventListener("keydown", e => {
    if (e.key === "Enter") send();
});

window.onload = () => {
add("Hey 🙂 I'm HappyMind. How are you feeling today?","bot")
}

function send() {
    const text = input.value.trim();
    if (!text) return;

    add(text, "user");
    input.value = "";

    showTyping();

    fetch("/chat", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({message: text})
})
.then(res => res.json())
.then(data => {
    removeTyping();

    console.log("Server response:", data);   // DEBUG LINE

    add(data.reply || "I'm here with you.", "bot");
})
.catch(error => {
    removeTyping();
    add("Something went wrong.", "bot");
});
}

function add(text, type) {
    const row = document.createElement("div");
    row.className = "message-row " + type;

    const avatar = document.createElement("img");
    avatar.className = "avatar";
    avatar.src = type === "bot" 
        ? "/static/images/bot.png" 
        : "/static/images/user.png";

    const bubble = document.createElement("div");
    bubble.className = "msg";
    bubble.innerText = text;

    if (type === "bot") {
        row.appendChild(avatar);
        row.appendChild(bubble);
    } else {
        row.appendChild(bubble);
        row.appendChild(avatar);
    }

    chat.appendChild(row);
    chat.scrollTop = chat.scrollHeight;
}

function showTyping() {
    const row = document.createElement("div");
    row.className = "message-row bot";
    row.id = "typing";

    const avatar = document.createElement("img");
    avatar.src = "/static/images/bot.png";
    avatar.className = "avatar";

    const bubble = document.createElement("div");
    bubble.className = "typing-dots";

    bubble.innerHTML = `
        <span></span>
        <span></span>
        <span></span>
    `;

    row.appendChild(avatar);
    row.appendChild(bubble);

    chat.appendChild(row);
    chat.scrollTop = chat.scrollHeight;
}

function removeTyping() {
    const t = document.getElementById("typing");
    if (t) t.remove();
}

function getMovies(){

fetch("/movies")
.then(res => res.json())
.then(data => add(data.reply,"bot"))

}

function getMusic(){

fetch("/music")
.then(res => res.json())
.then(data => add(data.reply,"bot"))

}

function getRelax(){

fetch("/relax")
.then(res => res.json())
.then(data => add(data.reply,"bot"))

}

function quickSuggest(type){

    let text = ""

    if(type === "suggest_movies") text = "Can you suggest some movies?"
    if(type === "suggest_music") text = "Can you suggest some relaxing music?"
    if(type === "suggest_relax") text = "Can you suggest something relaxing?"

    add(text,"user")

    showTyping()

    fetch("/chat",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({message:text})
    })
    .then(res=>res.json())
    .then(data=>{
        removeTyping()
        add(data.reply,"bot")
    })
}
/* FLOATING EMOJI BACKGROUND */

const emojiContainer = document.getElementById("emoji-bg");

const emojis = [
"🙂","😊","🌿","🌸","✨","💙","☁️","🧘","💫"
];

function createEmoji(){

    const emoji = document.createElement("div");
    emoji.classList.add("emoji");

    emoji.innerText = emojis[Math.floor(Math.random()*emojis.length)];

    emoji.style.left = Math.random()*100 + "vw";
    emoji.style.fontSize = (20 + Math.random()*25) + "px";
    emoji.style.animationDuration = (12 + Math.random()*10) + "s";

    emojiContainer.appendChild(emoji);

    setTimeout(()=>{
        emoji.remove();
    },20000);
}

setInterval(createEmoji,1500);