package edu.whimc.photographer.socket;

import java.util.UUID;

public class Response {

    private UUID clientUuid;
    private int observationId;
    private String feedback;
    private String generatedCaption;
    private float score;

    public Response() {
        super();
    }

    public Response(UUID clientUuid, int observationId, String feedback, String generatedCaption, float score) {
        this.clientUuid = clientUuid;
        this.observationId = observationId;
        this.feedback = feedback;
        this.generatedCaption = generatedCaption;
        this.score = score;
    }

    public UUID getClientUuid() {
        return clientUuid;
    }

    public int getObservationId() {
        return observationId;
    }

    public String getFeedback() {
        return feedback;
    }

    public String getGeneratedCaption() {
        return generatedCaption;
    }

    public float getScore() {
        return score;
    }
}
