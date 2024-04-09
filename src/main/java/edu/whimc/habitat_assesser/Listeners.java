package edu.whimc.habitat_assesser;

import com.corundumstudio.socketio.SocketIOClient;
import edu.whimc.overworld_agent.dialoguetemplate.events.BuildAssessEvent;
import org.bukkit.Bukkit;

import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;


public class Listeners implements Listener {

    private final HabitatAssesser plugin;

    public Listeners(HabitatAssesser plugin) {
        this.plugin = plugin;
    }

    @EventHandler
    public void onBuildAssessment(BuildAssessEvent assessment){
        this.plugin.queueAssessment(assessment);
    }
}
