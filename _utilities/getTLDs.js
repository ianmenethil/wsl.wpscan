function getTLDlist() {
	let tlds = [];
	let tds = document.querySelectorAll("td");
	for (let i = 0; i < tds.length; i++) {
		let tdText = tds[i].innerText;
		if (tdText[0] === "." && tdText.indexOf(" ") < 0 && tlds.indexOf(tdText) < 0) {
			tlds.push(tdText);
		}
	}
	return tlds;
}

function openPopup(content) {
	let outer = document.createElement("div");
	outer.style.position = "fixed";
	outer.style.width = "98%";
	outer.style.height = "96%";
	outer.style.top = "0";
	outer.style.left = "0";
	outer.style.zIndex = "9999999";
	let inner = document.createElement("textarea");
	inner.style.position = "absolute";
	inner.style.width = "100%";
	inner.style.height = "100%";
	inner.value = content;
	outer.appendChild(inner);
	document.body.appendChild(outer);
}

openPopup(
	"-------- newline-separated-tlds.txt --------\n" +
		getTLDlist().join("\n") +
		"\n\n\n\n-------- comma-separated-tlds.txt --------\n" +
		getTLDlist().join(",") +
		"\n\n\n\n-------- pipe-separated-tlds.txt --------\n" +
		getTLDlist().join("|")
);
