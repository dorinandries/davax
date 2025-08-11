import React from "react";
import { Chat } from "../../chat/Chat";
import Experience from "../../Experience";

const Scenes = ({ controlsEnabled = true, onProximity, nearAvatar }) => {
    return (
        <>
            <Experience
                controlsEnabled={controlsEnabled}
                onProximity={onProximity}
            />
            <Chat enabled={!!nearAvatar} mentor={nearAvatar} />
        </>
    );
};

export default Scenes;
