# How to Contribute

Python notebooks are the backbone of the automated UATs mechanism, because they are easy to write
and maintain. At the same time, however, they are a great way to provide examples that can be
directly tested and easily shared.

The `notebooks` directory will be continuously updated with new notebooks to test Kubeflow core
functionality and integrations. When adding new test notebooks you can use the existing ones for
reference in terms of style, coding conventions, and content. Below we provide some general
guidelines worth bearing in mind when contributing new notebooks.

## Notebook Guidelines

Notebooks added to the repository should serve both as tests and as examples, meant to be read by
users. With that in mind, they should be well-organised, including explanatory text where required.

At the same time, however, it is important that the notebooks perform verification checks
themselves. These checks should not affect the UX of manually executing the notebook. In fact, when
everything is as expected, their execution should be transparent to the user. It is in the event of
an error that they should raise an exception. This is crucial for the notebook execution engine to
be able to pick up and report any issues. Below you can find some guidelines fundamental to the
design of the test suite.

1. Use programmatic clients instead of CLI commands where possible. This makes programmatically
   inspecting the result of any action easier:

   ```bash
   # S3 CLI: hard to read, hard to parse its output
   !aws --endpoint-url $MINIO_ENDPOINT_URL s3 ls s3://bpk-nb-minio/
   # MinIO client: direct programmatic verification
   assert [obj for obj in mc.list_objects(BUCKET)] == [], f"Not empty!"
   ```

2. Add logic to wait for actions/runs to be completed
   * Use API calls instead of e.g. Selenium
   * Use `tenacity` to implement retries, e.g. waiting for a KFP run to complete and asserting it
     was successful:
		
      ```python
      @tenacity.retry(
          wait=tenacity.wait_exponential(multiplier=2, min=1, max=10),
          stop=tenacity.stop_after_attempt(30),
          reraise=True,
      )
      def assert_run_succeeded(kfp_client, run_id):
          """Wait for the run to complete successfully."""
          status = kfp_client.get_run(run_id).run.status
          assert status == "Succeeded", f"KFP run in {status} state."
      ```

3. Perform verification checks in separate cells
   * Use `assert` to enforce conditions of success
   * Mark verification cells with the `raises-exception` tag to instruct the execution engine to
     proceed with the rest of the notebook instead of exiting immediately:
     * Use the right-hand UI sidebar of Jupyterlab or
     * Edit the notebook JSON directly

4. Mark cells only destined for execution outside the automatic test suite with the `pytest-skip`
   tag
