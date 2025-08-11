export async function askPersona({ persona, userContext, question }) {
    const response = await fetch("http://localhost:8000/ask", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            persona,
            user_context: userContext,
            question,
        }),
    });

    if (!response.ok) throw new Error("Server error");
    return await response.json();
}
