import boto3
import botocore.config
import json
import logging

from datetime import datetime

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def blog_generate_using_bedrock(blogtopic: str) -> str:
    logger.info(":::: Generating blog 1 ..........")
    prompt = f"Write a 200-word blog post on the topic: {blogtopic}"

    logger.info(":::: Generating blog 2 ..........")
    # body = {"inputText": prompt, "textGenerationConfig":{"maxTokenCount": 3072, "temperature": 0.7, "topP": 0.9}}
    # body = "{\"inputText\":\"this is where you place your input text\",\"textGenerationConfig\":{\"maxTokenCount\":3072,\"stopSequences\":[],\"temperature\":0.7,\"topP\":0.9}}"

    logger.info(":::: Generating blog 2.1 ..........")
    logger.info(prompt)
    logger.info(":::: Generating blog 2.2 ..........")
    body = {
        "inputText": prompt,
        "textGenerationConfig": {
            "maxTokenCount": 500,
            "temperature": 0.7,
            "topP": 0.9,
            "stopSequences": [],
        },
    }
    logger.info(":::: Generating blog 3 ..........")
    try:
        bedrock = boto3.client(
            "bedrock-runtime",
            region_name="us-east-1",
            config=botocore.config.Config(
                read_timeout=300, retries={"max_attempts": 3}
            ),
        )
        logger.info(":::: Generating blog 4 ..........")

        response = bedrock.invoke_model(
            modelId="amazon.titan-text-premier-v1:0",
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )
        logger.info(":::: Generating blog 5 ..........")

        response_content = response.get("body").read()
        response_data = json.loads(response_content)
        logger.info(":::: Generating blog 6 ..........")
        logger.info("::::::::::::::::::: Response Data ::::::::::::::::::::::")
        logger.info(response_data)
        logger.info("::::::::::::::::::: End Response Data ::::::::::::::::::::::")
        blog_details = response_data["results"][0]["outputText"]
        return blog_details
    except Exception as e:
        logger.error(f"Error generating the blog: {e}", exc_info=True)
        return ""


def save_blog_details_s3(s3_key, s3_bucket, generate_blog):
    s3 = boto3.client("s3")

    try:
        s3.put_object(Bucket=s3_bucket, Key=s3_key, Body=generate_blog)
        logger.info("Blog saved to S3 successfully")

    except Exception as e:
        logger.error(f"Error when saving the blog to S3: {e}", exc_info=True)


def lambda_handler(event, context):
    logger.info(":::::::::::::::::LH:::::::::::::::::::::::::::")
    # logger.info(event)
    logger.info("Received event: %s", json.dumps(event))
    logger.info(":::::::::::::::::LH:::::::::::::::::::::::::::")

    try:
        logger.info(":::: Lambda handler 3 ")
        # raw_body = event.get("body")
        # if isinstance(raw_body, str):
        #     body = json.loads(raw_body)
        # else:
        #     body = raw_body

        body = event.get("body")
        if body is None:
            raise ValueError("Missing body in request")

        # Step 2: Convert string body to dict (if it's still a string)
        if isinstance(body, str):
            body = json.loads(body)

        blogtopic = body.get("blog_topic")
        logger.info(":::: Lambda handler 4 ")

        if not blogtopic:
            raise ValueError("Missing 'blog_topic' in request body")

        logger.info(":::: Lambda handler 5 ")

        generate_blog = blog_generate_using_bedrock(blogtopic=blogtopic)

        logger.info(":::: Lambda handler 6 ")

        if generate_blog:
            logger.info(":::: Lambda handler 3 - Blog generated successfully ")
            logger.info(
                f"Generated blog successfully: {generate_blog[:100]}..."
            )  # Log first 100 chars
            current_time = datetime.now().strftime("%H%M%S")
            s3_key = f"blog-output/{current_time}.txt"
            s3_bucket = "aws-bedrock-course1-clived"
            save_blog_details_s3(s3_key, s3_bucket, generate_blog)
            logger.info(":::: Lambda handler 4 - Blog saved successfully ")

        else:
            logger.warning("No blog was generated.")
    except Exception as e:
        logger.error(f"Error when handling event: {e}", exc_info=True)

    return {"statusCode": 200, "body": json.dumps("Blog Generation is completed")}
